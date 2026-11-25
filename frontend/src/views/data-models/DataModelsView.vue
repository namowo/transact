<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { StorageSerializers, useLocalStorage } from '@vueuse/core'
import { useToast } from '@nuxt/ui/composables'
import type { DropdownMenuItem } from '@nuxt/ui'
import {
  deleteDataModel,
  downloadDataModel,
  downloadDefinition,
  getCatalog,
  listDataModels,
} from '@/api/dataModels'
import { getErrorMessage } from '@/api/errors'
import type { Catalog, DataModel, ExportFormat } from '@/api/types'
import { requestDefinition } from '@/components/data-models/definition'
import StudyScopePicker from '@/components/data-models/StudyScopePicker.vue'
import { useConfirm } from '@/composables/useConfirm'
import { useLocalDataModels } from '@/composables/useLocalDataModels'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const toast = useToast()
const confirm = useConfirm()
const local = useLocalDataModels()

const models = ref<DataModel[]>([])
const catalog = ref<Catalog | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

async function load() {
  loading.value = true
  error.value = null
  local.reload()
  try {
    const [list, cat] = await Promise.all([listDataModels(), getCatalog()])
    models.value = list
    catalog.value = cat
  } catch (err) {
    error.value = getErrorMessage(err, "The data models couldn't be loaded.")
  } finally {
    loading.value = false
  }
}

onMounted(load)

const presets = computed(() => models.value.filter((m) => m.source === 'preset'))
const community = computed(() => models.value.filter((m) => m.source === 'public'))
const mine = computed(() =>
  auth.isAuthenticated ? models.value.filter((m) => m.source === 'mine') : local.models.value,
)

const datasetLabels = computed(
  () => new Map((catalog.value?.datasets ?? []).map((d) => [d.key, d.label])),
)

// Studies every download on this page is limited to. null: all available.
// Remembered in this browser so the choice survives a reload.
const studySelection = useLocalStorage<string[] | null>('transact-download-studies', null, {
  serializer: StorageSerializers.object,
})
const nothingSelected = computed(() => studySelection.value?.length === 0)

// Narrows a model's own study scope to the page selection - a model that
// is already limited to some studies keeps only the overlap.
function narrowed(model: DataModel) {
  const selected = studySelection.value
  if (!selected?.length) return model.definition
  const own = model.definition.study_ids
  return {
    ...model.definition,
    study_ids: own ? selected.filter((id) => own.includes(id)) : selected,
  }
}

const downloading = ref<string | null>(null)

async function download(model: DataModel, format: ExportFormat) {
  if (nothingSelected.value) return
  downloading.value = model.id
  try {
    if (model.source === 'local') {
      await downloadDefinition(requestDefinition(narrowed(model)), format, model.name)
    } else {
      await downloadDataModel(model.id, format, studySelection.value)
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

function remove(model: DataModel) {
  confirm.require({
    header: 'Delete data model?',
    message: `“${model.name}” will be deleted. Data you already downloaded is not affected.`,
    acceptLabel: 'Delete',
    acceptColor: 'error',
    accept: async () => {
      try {
        if (model.source === 'local') {
          local.remove(model.id)
        } else {
          await deleteDataModel(model.id)
          models.value = models.value.filter((m) => m.id !== model.id)
        }
        toast.add({ color: 'success', title: 'Data model deleted' })
      } catch (err) {
        toast.add({
          color: 'error',
          title: "Couldn't delete",
          description: getErrorMessage(err, 'Please try again.'),
        })
      }
    },
  })
}

function menuItems(model: DataModel) {
  const items: DropdownMenuItem[][] = [
    [
      {
        label: 'Download CSV',
        icon: 'i-lucide-file-text',
        disabled: nothingSelected.value,
        onSelect: () => download(model, 'csv'),
      },
      {
        label: 'Download Excel',
        icon: 'i-lucide-file-spreadsheet',
        disabled: nothingSelected.value,
        onSelect: () => download(model, 'xlsx'),
      },
    ],
  ]
  if (model.source === 'mine' || model.source === 'local') {
    items.push([
      { label: 'Delete', icon: 'i-lucide-trash-2', color: 'error', onSelect: () => remove(model) },
    ])
  }
  return items
}

const sections = computed(() => [
  {
    key: 'presets',
    title: 'Predefined',
    description: 'Ready-made data models for common questions. Open one to adjust it.',
    models: presets.value,
    empty: '',
  },
  {
    key: 'mine',
    title: auth.isAuthenticated ? 'My data models' : 'Saved in this browser',
    description: auth.isAuthenticated
      ? 'Your saved data models. Only you can see them unless you share them with the community.'
      : '',
    models: mine.value,
    empty: 'Nothing saved yet. Build a data model and save it to come back to it later.',
  },
  {
    key: 'community',
    title: 'Community',
    description: 'Data models other users have shared.',
    models: community.value,
    empty: 'No shared data models yet.',
  },
])
</script>

<template>
  <div class="flex flex-col gap-8">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div class="flex max-w-3xl flex-col gap-2">
        <h1 class="text-2xl font-bold">Data download</h1>
        <p class="text-sm text-muted">
          A data model describes which data you want - one row per result, contact, participant, …
          with the columns and filters you choose, across all available studies. It stores the
          query, not the data, so every download returns the latest data.
        </p>
      </div>
      <UButton icon="i-lucide-plus" label="New data model" :to="{ name: 'data-models-new' }" />
    </div>

    <UAlert
      v-if="!auth.isAuthenticated"
      color="info"
      variant="subtle"
      icon="i-lucide-info"
      title="Downloading without an account"
      description="You can download all published, quality-checked studies. Data models you save are kept in this browser only - sign in to keep them in your account, share them, and include your laboratory's own studies."
      :actions="[
        {
          label: 'Sign in',
          to: { name: 'login', query: { redirect: '/data' } },
          color: 'neutral',
          variant: 'outline',
        },
      ]"
    />

    <UAlert v-if="error" color="error" variant="subtle" :description="error" />

    <UCard>
      <div class="flex flex-col gap-3">
        <div>
          <h2 class="text-lg font-semibold">Studies to download</h2>
          <p class="text-sm text-muted">
            Limit every download on this page to the studies you need instead of downloading
            everything. Data models that are already limited to certain studies keep only the
            overlap.
          </p>
        </div>
        <StudyScopePicker
          v-model="studySelection"
          all-description="Downloads include every study available to you."
        />
        <UAlert
          v-if="nothingSelected"
          color="warning"
          variant="subtle"
          icon="i-lucide-triangle-alert"
          description="Choose at least one study to download data."
        />
      </div>
    </UCard>

    <div v-if="loading" class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <USkeleton v-for="n in 6" :key="n" class="h-40" />
    </div>

    <template v-else>
      <section
        v-for="section in sections"
        v-show="section.models.length || section.empty"
        :key="section.key"
        class="flex flex-col gap-3"
      >
        <div>
          <h2 class="text-lg font-semibold">{{ section.title }}</h2>
          <p v-if="section.description" class="text-sm text-muted">{{ section.description }}</p>
        </div>

        <p v-if="!section.models.length" class="text-sm text-muted">{{ section.empty }}</p>

        <div v-else class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <UCard
            v-for="model in section.models"
            :key="model.id"
            class="flex flex-col"
            :ui="{ body: 'flex flex-1 flex-col gap-3', footer: 'flex items-center gap-2' }"
          >
            <div class="flex flex-col gap-1">
              <RouterLink
                :to="{ name: 'data-models-edit', params: { id: model.id } }"
                class="font-semibold hover:text-primary"
              >
                {{ model.name }}
              </RouterLink>
              <p v-if="model.description" class="line-clamp-3 text-sm text-muted">
                {{ model.description }}
              </p>
            </div>
            <div class="mt-auto flex flex-wrap gap-1.5">
              <UBadge
                :label="datasetLabels.get(model.definition.dataset) ?? model.definition.dataset"
                variant="subtle"
                color="neutral"
                icon="i-lucide-rows-3"
              />
              <UBadge
                :label="`${model.definition.columns.length} columns`"
                variant="subtle"
                color="neutral"
              />
              <UBadge
                v-if="model.definition.filters.length"
                :label="`${model.definition.filters.length} ${model.definition.filters.length === 1 ? 'filter' : 'filters'}`"
                variant="subtle"
                color="neutral"
                icon="i-lucide-filter"
              />
              <UBadge
                v-if="model.source === 'mine' && model.is_public"
                label="Public"
                variant="subtle"
                color="success"
              />
              <UBadge
                v-if="model.source === 'public' && model.owner_name"
                :label="model.owner_name"
                variant="subtle"
                color="info"
                icon="i-lucide-user"
              />
            </div>

            <template #footer>
              <UButton
                label="Open"
                variant="soft"
                color="neutral"
                icon="i-lucide-sliders-horizontal"
                :to="{ name: 'data-models-edit', params: { id: model.id } }"
              />
              <UButton
                label="CSV"
                variant="ghost"
                color="neutral"
                icon="i-lucide-download"
                :loading="downloading === model.id"
                :disabled="nothingSelected"
                @click="download(model, 'csv')"
              />
              <UDropdownMenu :items="menuItems(model)" :content="{ align: 'end' }">
                <UButton
                  variant="ghost"
                  color="neutral"
                  icon="i-lucide-ellipsis"
                  aria-label="More actions"
                  class="ms-auto"
                />
              </UDropdownMenu>
            </template>
          </UCard>
        </div>
      </section>
    </template>
  </div>
</template>
