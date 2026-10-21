<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import { FilterMatchMode } from '@openvue/core/api'
import DataTableSkeleton from '@/components/data/DataTableSkeleton.vue'
import EntitySelect from '@/components/scenarios/EntitySelect.vue'
import InlineCreatableSelect from '@/components/scenarios/InlineCreatableSelect.vue'
import NamedCategoryRadioGroup from '@/components/scenarios/NamedCategoryRadioGroup.vue'
import SurfaceMultiSelect from './SurfaceMultiSelect.vue'
import { surfaceLabel, recoverySetLabel, extractionMethodLabel } from './recoveryLabel'
import { recoveryApi, recoverySetApi, samplingMethodApi, extractionMethodApi } from '@/api/methods'
import { experienceLevelCategoryApi } from '@/api/categories'
import type {
  Contact,
  ContactTemplate,
  Recovery,
  RecoveryInput,
  RecoverySet,
  SamplingMethod,
  ExtractionMethod,
  Surface,
} from '@/api/types'

const props = defineProps<{
  studyId: string
  contacts: Contact[]
  contactTemplates: ContactTemplate[]
}>()

const emit = defineEmits<{
  'update:recoveries': [recoveries: Recovery[]]
}>()

const experienceLevelIcons: Record<string, string> = {
  low: 'i-lucide-signal-low',
  medium: 'i-lucide-signal-medium',
  high: 'i-lucide-signal-high',
}

const studySurfaces = computed<Surface[]>(() => {
  const bySurfaceId = new Map<string, Surface>()
  for (const contact of props.contacts) {
    if (contact.donor_surface) bySurfaceId.set(contact.donor_surface.id, contact.donor_surface)
    if (contact.recipient_surface)
      bySurfaceId.set(contact.recipient_surface.id, contact.recipient_surface)
  }
  return Array.from(bySurfaceId.values())
})

const studySurfaceIds = computed(() => new Set(studySurfaces.value.map((s) => s.id)))

const allRecoveries = ref<Recovery[]>([])
const loading = ref(false)
const loadError = ref('')

const recoveries = computed(() =>
  allRecoveries.value.filter(
    (recovery) => recovery.surface_id != null && studySurfaceIds.value.has(recovery.surface_id),
  ),
)

watch(recoveries, (value) => emit('update:recoveries', value), { immediate: true })

const recoverySets = ref<RecoverySet[]>([])

// Recoveries with no recovery_set_id are grouped under a single "Ungrouped"
// bucket so the table always groups consistently.
const groupedRecoveries = computed(() => {
  const groups = new Map<string | null, Recovery[]>()
  for (const recovery of recoveries.value) {
    const key = recovery.recovery_set_id ?? null
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push(recovery)
  }
  return Array.from(groups.entries()).map(([recoverySetId, items]) => ({
    recoverySetId,
    recoverySet: recoverySets.value.find((set) => set.id === recoverySetId) ?? null,
    items,
  }))
})

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const [recoveryResults, recoverySetResults] = await Promise.all([
      recoveryApi.list(),
      recoverySetApi.list(),
    ])
    allRecoveries.value = recoveryResults
    recoverySets.value = recoverySetResults
  } catch {
    loadError.value = 'Could not load recoveries. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

function initFilters() {
  return {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
    'extraction_method.extraction_protocol': { value: null, matchMode: FilterMatchMode.CONTAINS },
    elution_volume: { value: null, matchMode: FilterMatchMode.CONTAINS },
    area: { value: null, matchMode: FilterMatchMode.CONTAINS },
  }
}

const filters = ref(initFilters())

function clearFilters() {
  filters.value = initFilters()
}

const samplingMethods = ref<SamplingMethod[]>([])
const extractionMethods = ref<ExtractionMethod[]>([])

onMounted(async () => {
  samplingMethods.value = await samplingMethodApi.list()
  extractionMethods.value = await extractionMethodApi.list()
})

function emptyForm(): RecoveryInput {
  return {
    study_id: props.studyId,
    recovery_set_id: null,
    surface_id: null,
    sampling_method_id: null,
    extraction_method_id: null,
    elution_volume: null,
    area: null,
    experience_level_of_sampler_id: null,
  }
}

// In create mode, a recovery is made per selected surface, so surface_id
// isn't part of the validated form - surfaceIds below covers it instead.
const schema = yup.object({
  study_id: yup.string().nullable().defined(),
  recovery_set_id: yup.string().nullable().defined(),
  surface_id: yup.string().nullable().defined(),
  sampling_method_id: yup.string().nullable().defined(),
  extraction_method_id: yup.string().nullable().defined(),
  elution_volume: yup.number().nullable().min(0, 'Elution volume must be zero or greater.'),
  area: yup.number().nullable().min(0, 'Area must be zero or greater.'),
  experience_level_of_sampler_id: yup.string().nullable().defined(),
})

const { defineField, errors, handleSubmit, resetForm } = useForm<RecoveryInput>({
  validationSchema: schema,
  initialValues: emptyForm(),
})

const [surfaceId] = defineField('surface_id')
const [recoverySetId] = defineField('recovery_set_id')
const [samplingMethodId] = defineField('sampling_method_id')
const [extractionMethodId] = defineField('extraction_method_id')
const [elutionVolume] = defineField('elution_volume')
const [area] = defineField('area')
const [experienceLevelOfSamplerId] = defineField('experience_level_of_sampler_id')

const surfaceIds = ref<string[]>([])

const dialogVisible = ref(false)
const editingId = ref<string | null>(null)
const submitting = ref(false)
const submitError = ref('')

function openCreateDialog() {
  editingId.value = null
  resetForm({ values: emptyForm() })
  surfaceIds.value = []
  submitError.value = ''
  dialogVisible.value = true
}

function openEditDialog(row: Recovery) {
  editingId.value = row.id
  resetForm({
    values: {
      study_id: row.study_id ?? props.studyId,
      recovery_set_id: row.recovery_set_id ?? null,
      surface_id: row.surface_id ?? null,
      sampling_method_id: row.sampling_method_id ?? null,
      extraction_method_id: row.extraction_method_id ?? null,
      elution_volume: row.elution_volume ?? null,
      area: row.area ?? null,
      experience_level_of_sampler_id: row.experience_level_of_sampler_id ?? null,
    },
  })
  surfaceIds.value = row.surface_id ? [row.surface_id] : []
  submitError.value = ''
  dialogVisible.value = true
}

const canSave = computed(() =>
  editingId.value === null ? surfaceIds.value.length > 0 : true,
)

const submitForm = handleSubmit(async (formValues) => {
  submitting.value = true
  submitError.value = ''
  try {
    if (editingId.value === null) {
      const created = await Promise.all(
        surfaceIds.value.map((surface_id) => recoveryApi.create({ ...formValues, surface_id })),
      )
      allRecoveries.value = [...allRecoveries.value, ...created]
    } else {
      const updated = await recoveryApi.update(editingId.value, {
        ...formValues,
        surface_id: surfaceIds.value[0] ?? null,
      })
      allRecoveries.value = allRecoveries.value.map((item) =>
        item.id === updated.id ? updated : item,
      )
    }
    dialogVisible.value = false
  } catch {
    submitError.value = 'Could not save these recoveries. Please try again.'
  } finally {
    submitting.value = false
  }
})

async function deleteRow(row: Recovery) {
  if (!window.confirm('Delete this recovery? This cannot be undone.')) return
  try {
    await recoveryApi.delete(row.id)
    allRecoveries.value = allRecoveries.value.filter((item) => item.id !== row.id)
  } catch {
    loadError.value = 'Could not delete this recovery. Please try again.'
  }
}

async function createRecoverySet(name: string) {
  return recoverySetApi.create({ name: name || null })
}

function onRecoverySetCreated(created: { id: string; name?: string | null }) {
  recoverySets.value = [...recoverySets.value, created as RecoverySet]
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-between">
      <p class="text-sm text-surface-500 dark:text-surface-400">
        Samples recovered from this study's actual contacts' surfaces.
      </p>
      <UButton
        label="Add recovery"
        icon="i-lucide-plus"
        variant="outline"
        :disabled="!studySurfaces.length"
        @click="openCreateDialog"
      />
    </div>

    <UAlert
      v-if="!studySurfaces.length"
      color="info"
      variant="outline"
      description="Add an actual contact before recording recoveries."
    />

    <UAlert v-if="loadError" color="error" variant="outline" :description="loadError" />

    <div class="flex items-center justify-between gap-3">
      <UButton type="button" icon="i-lucide-filter-x" variant="outline" size="sm" @click="clearFilters()">
        Clear Filters
      </UButton>
      <UInput
        v-model="filters['global'].value"
        type="text"
        icon="i-lucide-search"
        placeholder="Keyword Search"
      />
    </div>

    <DataTableSkeleton v-if="loading" :columns="5" />

    <div
      v-else
      v-for="group in groupedRecoveries"
      :key="group.recoverySetId ?? 'ungrouped'"
      class="flex flex-col gap-2"
    >
      <h4 class="font-medium text-sm">
        {{ group.recoverySetId === null ? 'Ungrouped' : recoverySetLabel(group.recoverySet) }}
      </h4>
      <div class="overflow-x-auto">
        <DataTable
          v-model:filters="filters"
          :value="group.items"
          data-key="id"
          filterDisplay="menu"
          :globalFilterFields="['extraction_method.extraction_protocol', 'elution_volume', 'area']"
        >
          <Column header="Surface">
            <template #body="{ data }">{{ surfaceLabel(data.surface) }}</template>
          </Column>
          <Column header="Sampling method">
            <template #body="{ data }">{{ data.sampling_method ? `#${data.sampling_method.id}` : '—' }}</template>
          </Column>
          <Column
            field="extraction_method.extraction_protocol"
            header="Extraction method"
            sortable
            :showFilterOperator="false"
            :showAddButton="false"
          >
            <template #body="{ data }">{{ extractionMethodLabel(data.extraction_method) }}</template>
            <template #filter="{ filterModel }">
              <UInput v-model="filterModel.value" type="text" placeholder="Search by extraction method" />
            </template>
          </Column>
          <Column
            field="elution_volume"
            header="Elution volume"
            sortable
            :showFilterOperator="false"
            :showAddButton="false"
          >
            <template #filter="{ filterModel }">
              <UInput v-model="filterModel.value" type="text" placeholder="Search by elution volume" />
            </template>
          </Column>
          <Column
            field="area"
            header="Area"
            sortable
            :showFilterOperator="false"
            :showAddButton="false"
          >
            <template #filter="{ filterModel }">
              <UInput v-model="filterModel.value" type="text" placeholder="Search by area" />
            </template>
          </Column>
          <Column header="" style="width: 6rem">
            <template #body="{ data }">
              <div class="flex gap-1 justify-end">
                <UButton icon="i-lucide-pencil" variant="ghost" square aria-label="Edit" @click="openEditDialog(data)" />
                <UButton
                  icon="i-lucide-trash-2"
                  variant="ghost"
                  square
                  color="error"
                  aria-label="Delete"
                  @click="deleteRow(data)"
                />
              </div>
            </template>
          </Column>
        </DataTable>
      </div>
    </div>

    <UModal
      v-model:open="dialogVisible"
      :title="editingId === null ? 'Add recovery' : 'Edit recovery'"
      :ui="{ content: 'max-w-2xl', footer: 'justify-end' }"
    >
      <template #body>
        <div class="flex flex-col gap-4">
          <UFormField
            v-if="editingId === null"
            label="Surfaces"
            hint="One recovery is created per selected surface"
          >
            <SurfaceMultiSelect
              v-model="surfaceIds"
              :contacts="props.contacts"
              :contact-templates="contactTemplates"
            />
          </UFormField>
          <EntitySelect
            v-else
            v-model="surfaceId"
            label="Surface"
            :options="studySurfaces"
            :option-label="surfaceLabel"
            :error="errors.surface_id"
          />
          <UFormField label="Recovery set" hint="Optional">
            <InlineCreatableSelect
              v-model="recoverySetId"
              :options="recoverySets.map((s) => ({ id: s.id, name: recoverySetLabel(s) }))"
              :create="createRecoverySet"
              @created="onRecoverySetCreated"
            />
          </UFormField>
          <EntitySelect
            v-model="samplingMethodId"
            label="Sampling method"
            :options="samplingMethods"
            :option-label="(m: SamplingMethod) => `#${m.id}`"
          />
          <p v-if="!samplingMethods.length" class="text-sm text-surface-500 dark:text-surface-400 -mt-2">
            No sampling methods yet. Add one under
            <RouterLink :to="{ name: 'settings-methods-sampling' }" class="underline" target="_blank">
              Settings → Methods → Sampling
            </RouterLink>.
          </p>
          <EntitySelect
            v-model="extractionMethodId"
            label="Extraction method"
            :options="extractionMethods"
            :option-label="extractionMethodLabel"
          />
          <p v-if="!extractionMethods.length" class="text-sm text-surface-500 dark:text-surface-400 -mt-2">
            No extraction methods yet. Add one under
            <RouterLink :to="{ name: 'settings-methods-extraction' }" class="underline" target="_blank">
              Settings → Methods → Extraction
            </RouterLink>.
          </p>
          <UFormField label="Elution volume" :error="errors.elution_volume">
            <UFieldGroup>
              <UInputNumber v-model="elutionVolume" orientation="vertical" class="w-full" />
              <UBadge color="neutral" variant="outline" size="lg" label="µL" />
            </UFieldGroup>
          </UFormField>
          <UFormField label="Area" :error="errors.area">
            <UFieldGroup>
              <UInputNumber v-model="area" orientation="vertical" class="w-full" />
              <UBadge color="neutral" variant="outline" size="lg" label="cm²" />
            </UFieldGroup>
          </UFormField>
          <NamedCategoryRadioGroup
            v-model="experienceLevelOfSamplerId"
            label="Experience level of sampler"
            :api="experienceLevelCategoryApi"
            :icons="experienceLevelIcons"
            orientation="horizontal"
          />

          <UAlert v-if="submitError" color="error" variant="outline" :description="submitError" />
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="dialogVisible = false" />
        <UButton
          :label="editingId === null && surfaceIds.length > 1
            ? `Save ${surfaceIds.length} recoveries`
            : 'Save'"
          icon="i-lucide-save"
          :loading="submitting"
          :disabled="!canSave"
          @click="submitForm"
        />
      </template>
    </UModal>
  </div>
</template>
