<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { useToast } from '@nuxt/ui/composables'
import {
  createDataModel,
  dataModelDownloadUrl,
  downloadDataModel,
  downloadDefinition,
  getCatalog,
  getDataModel,
  previewDataModel,
  updateDataModel,
} from '@/api/dataModels'
import { getErrorMessage } from '@/api/errors'
import type {
  Catalog,
  DataModel,
  DataModelDefinition,
  DataModelPreview,
  ExportFormat,
} from '@/api/types'
import ColumnPicker from '@/components/data-models/ColumnPicker.vue'
import FilterEditor from '@/components/data-models/FilterEditor.vue'
import SaveDataModelModal, {
  type SaveDetails,
} from '@/components/data-models/SaveDataModelModal.vue'
import PreviewPanel from '@/components/data-models/PreviewPanel.vue'
import StudyScopePicker from '@/components/data-models/StudyScopePicker.vue'
import TablePicker from '@/components/data-models/TablePicker.vue'
import {
  addJoin,
  emptyDefinition,
  isFilterComplete,
  joinedFields,
  removeJoin,
  requestDefinition,
  switchDataset,
  withJoins,
} from '@/components/data-models/definition'
import { decodeSharedModel, encodeSharedModel } from '@/components/data-models/shareLink'
import { useConfirm } from '@/composables/useConfirm'
import { isLocalId, useLocalDataModels } from '@/composables/useLocalDataModels'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{ id?: string }>()

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const toast = useToast()
const confirm = useConfirm()
const local = useLocalDataModels()

const catalog = ref<Catalog | null>(null)
const loadError = ref<string | null>(null)
const loading = ref(true)

// The saved model being edited, if any.
const model = ref<DataModel | null>(null)
const name = ref('')
const description = ref<string | null>(null)
const isPublic = ref(false)
const definition = ref<DataModelDefinition | null>(null)
const snapshot = ref('')

function currentState() {
  return JSON.stringify({
    name: name.value,
    description: description.value,
    definition: definition.value,
  })
}

const dirty = computed(() => !!definition.value && currentState() !== snapshot.value)

function apply(source: {
  name: string
  description?: string | null
  definition: DataModelDefinition
}) {
  name.value = source.name
  description.value = source.description ?? null
  const ds = catalog.value?.datasets.find((d) => d.key === source.definition.dataset)
  const copy = structuredClone(source.definition)
  definition.value = ds ? withJoins(copy, ds) : copy
}

async function load() {
  loading.value = true
  loadError.value = null
  model.value = null
  try {
    catalog.value = await getCatalog()
    if (props.id) {
      const found = isLocalId(props.id) ? local.get(props.id) : await getDataModel(props.id)
      if (!found) throw new Error('not found')
      model.value = found
      isPublic.value = found.is_public
      apply(found)
    } else if (typeof route.query.m === 'string') {
      const shared = decodeSharedModel(route.query.m)
      if (!shared) {
        loadError.value =
          "This share link can't be read. It may have been cut off when it was copied."
        return
      }
      isPublic.value = false
      apply(shared)
    } else {
      const requested = catalog.value.datasets.find((d) => d.key === route.query.dataset)
      isPublic.value = false
      apply({
        name: 'New data model',
        definition: emptyDefinition(requested ?? catalog.value.datasets[0]!),
      })
    }
    snapshot.value = currentState()
  } catch (err) {
    loadError.value = getErrorMessage(
      err,
      "This data model doesn't exist or isn't shared with you.",
    )
  } finally {
    loading.value = false
  }
}

watch(() => [props.id, route.query.m], load, { immediate: true })

const dataset = computed(
  () => catalog.value?.datasets.find((d) => d.key === definition.value?.dataset) ?? null,
)

const datasetItems = computed(() =>
  (catalog.value?.datasets ?? []).map((d) => ({
    label: d.label,
    value: d.key,
    description: d.description,
  })),
)

function setDataset(key: unknown) {
  const next = catalog.value?.datasets.find((d) => d.key === key)
  if (next && definition.value) definition.value = switchDataset(definition.value, next)
}

// Columns and filters can only use the joined tables.
const availableFields = computed(() =>
  dataset.value && definition.value ? joinedFields(dataset.value, definition.value.joins) : [],
)

function toggleJoin(key: string, on: boolean) {
  const ds = dataset.value
  if (!ds || !definition.value) return
  if (on) {
    definition.value = addJoin(definition.value, ds, key)
    return
  }
  const result = removeJoin(definition.value, ds, key)
  definition.value = result.definition
  const removed = [
    result.removedColumns &&
      `${result.removedColumns} ${result.removedColumns === 1 ? 'column' : 'columns'}`,
    result.removedFilters &&
      `${result.removedFilters} ${result.removedFilters === 1 ? 'filter' : 'filters'}`,
  ].filter(Boolean)
  if (removed.length) {
    toast.add({
      color: 'neutral',
      icon: 'i-lucide-unlink',
      title: `Removed ${removed.join(' and ')}`,
      description: 'They came from the table you removed.',
    })
  }
}

const canSaveInPlace = computed(
  () => model.value?.source === 'mine' || model.value?.source === 'local',
)

const sourceBadge = computed(() => {
  switch (model.value?.source) {
    case 'preset':
      return { label: 'Predefined', color: 'primary' as const }
    case 'public':
      return {
        label: model.value.owner_name ? `Shared by ${model.value.owner_name}` : 'Community',
        color: 'info' as const,
      }
    case 'local':
      return { label: 'Saved in this browser', color: 'neutral' as const }
    case 'mine':
      return isPublic.value
        ? { label: 'Public', color: 'success' as const }
        : { label: 'Private', color: 'neutral' as const }
    default:
      return null
  }
})

// --- Preview -------------------------------------------------------------------

// The preview only loads on demand, from the panel at the bottom.
const previewOpen = ref(false)
const preview = ref<DataModelPreview | null>(null)
const previewError = ref<string | null>(null)
const previewLoading = ref(false)
const previewedKey = ref<string | null>(null)
let previewAbort: AbortController | null = null

const previewKey = computed(() =>
  definition.value ? JSON.stringify(requestDefinition(definition.value)) : '',
)
const previewStale = computed(
  () => previewedKey.value !== null && previewedKey.value !== previewKey.value,
)

const skippedFilters = computed(
  () => definition.value?.filters.filter((f) => !isFilterComplete(f)).length ?? 0,
)

async function runPreview() {
  if (!definition.value) return
  previewAbort?.abort()
  if (!definition.value.columns.length) {
    preview.value = null
    previewError.value = 'Pick at least one column to see a preview.'
    return
  }
  const controller = new AbortController()
  previewAbort = controller
  previewLoading.value = true
  previewedKey.value = previewKey.value
  try {
    preview.value = await previewDataModel(requestDefinition(definition.value), controller.signal)
    previewError.value = null
  } catch (err) {
    if (controller.signal.aborted) return
    previewError.value = getErrorMessage(err, "The preview couldn't be loaded.")
  } finally {
    if (previewAbort === controller) previewLoading.value = false
  }
}

// A different model is a fresh start: no preview until asked for.
watch(
  () => [props.id, route.query.m],
  () => {
    previewAbort?.abort()
    preview.value = null
    previewError.value = null
    previewedKey.value = null
  },
)

// --- Saving --------------------------------------------------------------------

const saveOpen = ref(false)
const saveMode = ref<'update' | 'create'>('create')
const saving = ref(false)

const saveInitial = computed<SaveDetails>(() => ({
  name: saveMode.value === 'create' && model.value ? `Copy of ${name.value}` : name.value,
  description: description.value,
  is_public: saveMode.value === 'update' ? isPublic.value : false,
}))

function openSave(mode: 'update' | 'create') {
  saveMode.value = mode
  saveOpen.value = true
}

async function save(details: SaveDetails) {
  if (!definition.value) return
  saving.value = true
  const payload = { ...details, definition: definition.value }
  try {
    let saved: DataModel | null
    if (saveMode.value === 'update' && model.value?.source === 'local') {
      saved = local.update(model.value.id, payload)
    } else if (saveMode.value === 'update' && model.value?.source === 'mine') {
      saved = await updateDataModel(model.value.id, payload)
    } else if (auth.isAuthenticated) {
      saved = await createDataModel(payload)
    } else {
      saved = local.create(payload)
    }
    if (!saved) throw new Error('not saved')
    model.value = saved
    isPublic.value = saved.is_public
    apply(saved)
    snapshot.value = currentState()
    saveOpen.value = false
    toast.add({ color: 'success', title: 'Data model saved', icon: 'i-lucide-check' })
    if (props.id !== saved.id) {
      await router.replace({ name: 'data-models-edit', params: { id: saved.id } })
    }
  } catch (err) {
    toast.add({
      color: 'error',
      title: "Couldn't save the data model",
      description: getErrorMessage(err, 'Please try again.'),
    })
  } finally {
    saving.value = false
  }
}

// --- Download & sharing ----------------------------------------------------------

const downloading = ref<ExportFormat | null>(null)

async function download(format: ExportFormat) {
  if (!definition.value) return
  downloading.value = format
  try {
    // Saved models are fetched by id, so the Excel "About" sheet can link
    // back to them; anything unsaved is sent along.
    if (model.value && model.value.source !== 'local' && !dirty.value) {
      await downloadDataModel(model.value.id, format)
    } else {
      await downloadDefinition(requestDefinition(definition.value), format, name.value)
    }
  } catch (err) {
    toast.add({
      color: 'error',
      title: 'Download failed',
      description: getErrorMessage(err, 'Please try again.'),
    })
  } finally {
    downloading.value = null
  }
}

const downloadItems = computed(() => [
  {
    label: 'CSV',
    description: 'For R, Python and any spreadsheet',
    icon: 'i-lucide-file-text',
    onSelect: () => download('csv'),
  },
  {
    label: 'Excel (.xlsx)',
    description: 'Includes a sheet listing the studies to cite',
    icon: 'i-lucide-file-spreadsheet',
    onSelect: () => download('xlsx'),
  },
])

const shareableById = computed(
  () =>
    !!model.value &&
    !dirty.value &&
    (model.value.source === 'preset' ||
      model.value.source === 'public' ||
      (model.value.source === 'mine' && isPublic.value)),
)

async function copyShareLink() {
  if (!definition.value) return
  const target = shareableById.value
    ? router.resolve({ name: 'data-models-edit', params: { id: model.value!.id } })
    : router.resolve({
        name: 'data-models-new',
        query: {
          m: encodeSharedModel({
            name: name.value,
            description: description.value,
            definition: requestDefinition(definition.value),
          }),
        },
      })
  const url = new URL(target.href, window.location.origin).toString()
  try {
    await navigator.clipboard.writeText(url)
    toast.add({
      color: 'success',
      icon: 'i-lucide-link',
      title: 'Link copied',
      description: shareableById.value
        ? 'Anyone with the link can open this data model.'
        : 'The link carries the model itself. Recipients only download data from studies available to them.',
    })
  } catch {
    toast.add({ color: 'error', title: "Couldn't copy the link", description: url })
  }
}

const scriptUrl = computed(() =>
  model.value && model.value.source !== 'local' ? dataModelDownloadUrl(model.value.id) : null,
)

const scriptSnippet = computed(() =>
  scriptUrl.value
    ? `curl -H "Authorization: Bearer <your API key>" \\\n  "${scriptUrl.value}" -o data.csv`
    : '',
)

async function copySnippet() {
  try {
    await navigator.clipboard.writeText(scriptSnippet.value)
    toast.add({ color: 'success', title: 'Command copied', icon: 'i-lucide-check' })
  } catch {
    toast.add({ color: 'error', title: "Couldn't copy the command" })
  }
}

// --- Leaving with unsaved changes --------------------------------------------------

onBeforeRouteLeave((to) => {
  // Saving a new model replaces the route with its id; that's not leaving.
  if (!dirty.value || saving.value || to.name === 'data-models-edit') return true
  return new Promise<boolean>((resolve) =>
    confirm.require({
      header: 'Discard changes?',
      message: 'Your changes to this data model are not saved.',
      acceptLabel: 'Discard',
      rejectLabel: 'Keep editing',
      acceptColor: 'error',
      accept: () => resolve(true),
      reject: () => resolve(false),
    }),
  )
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <div v-if="loading" class="flex flex-col gap-4">
      <USkeleton class="h-8 w-72" />
      <USkeleton class="h-96 w-full" />
    </div>

    <UEmpty
      v-else-if="loadError || !definition || !dataset || !catalog"
      icon="i-lucide-database-zap"
      title="Data model not available"
      :description="loadError ?? undefined"
      :actions="[
        { label: 'All data models', icon: 'i-lucide-arrow-left', to: { name: 'data-models' } },
      ]"
    />

    <template v-else>
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div class="flex min-w-0 flex-col gap-1">
          <div class="flex flex-wrap items-center gap-2">
            <h1 class="text-2xl font-bold">{{ name }}</h1>
            <UBadge
              v-if="sourceBadge"
              :label="sourceBadge.label"
              :color="sourceBadge.color"
              variant="subtle"
            />
            <UBadge
              v-if="dirty && model"
              label="Unsaved changes"
              color="warning"
              variant="subtle"
            />
          </div>
          <p v-if="description" class="max-w-3xl text-sm text-muted whitespace-pre-line">
            {{ description }}
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <UButton
            variant="ghost"
            color="neutral"
            icon="i-lucide-link"
            label="Copy link"
            @click="copyShareLink"
          />
          <UButton
            v-if="model && canSaveInPlace"
            variant="ghost"
            color="neutral"
            icon="i-lucide-copy"
            label="Save as copy"
            @click="openSave('create')"
          />
          <UButton
            variant="outline"
            color="neutral"
            icon="i-lucide-save"
            :label="canSaveInPlace ? 'Save' : model ? 'Save as copy' : 'Save'"
            @click="openSave(canSaveInPlace ? 'update' : 'create')"
          />
          <UDropdownMenu :items="downloadItems" :content="{ align: 'end' }">
            <UButton
              icon="i-lucide-download"
              label="Download"
              trailing-icon="i-lucide-chevron-down"
              :loading="!!downloading"
              :disabled="!definition.columns.length"
            />
          </UDropdownMenu>
        </div>
      </div>

      <UAlert
        v-if="model && !canSaveInPlace"
        color="info"
        variant="subtle"
        icon="i-lucide-info"
        :description="
          model.source === 'preset'
            ? 'This is a predefined data model. Adjust it freely - to keep your changes, save a copy.'
            : 'This data model is shared by another user. To keep your changes, save a copy.'
        "
      />

      <div class="flex flex-col gap-4">
        <UCard>
          <template #header>
            <h2 class="font-semibold">1. Start from</h2>
            <p class="text-xs text-muted">What is one row of your data?</p>
          </template>
          <URadioGroup
            :model-value="definition.dataset"
            :items="datasetItems"
            variant="card"
            :ui="{ fieldset: 'grid gap-2 sm:grid-cols-2' }"
            @update:model-value="setDataset"
          />
        </UCard>

        <UCard>
          <template #header>
            <h2 class="font-semibold">2. Tables</h2>
            <p class="text-xs text-muted">
              Join the tables you need columns or filters from. Joining adds columns, never rows -
              you still get one row per entry in “{{ dataset.label }}”.
            </p>
          </template>
          <TablePicker
            :dataset="dataset"
            :joins="definition.joins ?? []"
            :columns="definition.columns"
            @toggle="toggleJoin"
          />
        </UCard>
        <UCard>
          <template #header>
            <h2 class="font-semibold">3. Columns</h2>
          </template>
          <ColumnPicker v-model="definition.columns" :fields="availableFields" />
        </UCard>

        <UCard>
          <template #header>
            <h2 class="font-semibold">4. Filters</h2>
            <p class="text-xs text-muted">Filters apply across all included studies.</p>
          </template>
          <FilterEditor
            v-model="definition.filters"
            :dataset="dataset"
            :fields="availableFields"
            :operators="catalog.operators"
          />
        </UCard>

        <UCard>
          <template #header>
            <h2 class="font-semibold">5. Studies</h2>
          </template>
          <StudyScopePicker v-model="definition.study_ids" />
        </UCard>

        <UCard v-if="scriptUrl">
          <template #header>
            <h2 class="font-semibold">Use in scripts</h2>
            <p class="text-xs text-muted">
              Fetch the latest data on every run - from R, Python or the command line. Create an API
              key in your
              <ULink :to="{ name: 'profile' }" class="text-primary">profile</ULink>; without one,
              only published, quality-checked data is returned.
            </p>
          </template>
          <div class="flex flex-col gap-2">
            <pre
              class="overflow-x-auto rounded-md bg-elevated p-3 text-xs"
            ><code>{{ scriptSnippet }}</code></pre>
            <UButton
              size="xs"
              variant="soft"
              color="neutral"
              icon="i-lucide-copy"
              label="Copy command"
              class="self-start"
              @click="copySnippet"
            />
            <p v-if="dirty" class="text-xs text-warning">
              Scripts use the saved version of this model - save to include your latest changes.
            </p>
          </div>
        </UCard>
      </div>

      <PreviewPanel
        v-model:open="previewOpen"
        :preview="preview"
        :loading="previewLoading"
        :error="previewError"
        :stale="previewStale"
        :skipped-filters="skippedFilters"
        @run="runPreview"
      />
    </template>

    <SaveDataModelModal
      v-model:open="saveOpen"
      :title="saveMode === 'update' ? 'Save data model' : 'Save as new data model'"
      :initial="saveInitial"
      :can-publish="auth.isAuthenticated"
      :saving="saving"
      @save="save"
    />
  </div>
</template>
