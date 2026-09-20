<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import CategorySelect from '@/components/scenarios/CategorySelect.vue'
import EntitySelect from '@/components/scenarios/EntitySelect.vue'
import { recoveryApi, recoverySetApi, samplingMethodApi, extractionMethodApi } from '@/api/methods'
import { experienceLevelCategoryApi } from '@/api/categories'
import type {
  Contact,
  Recovery,
  RecoveryInput,
  RecoverySet,
  SamplingMethod,
  ExtractionMethod,
  Surface,
} from '@/api/types'

const props = defineProps<{ studyId: string; contacts: Contact[] }>()

const emit = defineEmits<{
  'update:recoveries': [recoveries: Recovery[]]
}>()

function surfaceLabel(surface: Surface): string {
  const template = surface.surface_template
  const subject = surface.individual
    ? 'Individual'
    : (template?.item?.item_category?.name ?? 'Item')
  const part =
    surface.location_of_body_category?.name ??
    template?.location_of_body_category?.name ??
    surface.item_parts_category?.name ??
    template?.item_parts_category?.name ??
    null
  return [subject, part].filter(Boolean).join(' — ') || `Surface #${surface.id}`
}

const studySurfaces = computed<Surface[]>(() => {
  const bySurfaceId = new Map<number, Surface>()
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
  const groups = new Map<number | null, Recovery[]>()
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

const schema = yup.object({
  study_id: yup.string().nullable().defined(),
  recovery_set_id: yup.string().nullable().defined(),
  surface_id: yup.string().nullable().required('Please select a surface.'),
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

const dialogVisible = ref(false)
const editingId = ref<string | null>(null)
const submitting = ref(false)
const submitError = ref('')

function openCreateDialog() {
  editingId.value = null
  resetForm({ values: emptyForm() })
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
  submitError.value = ''
  dialogVisible.value = true
}

const submitForm = handleSubmit(async (formValues) => {
  submitting.value = true
  submitError.value = ''
  try {
    if (editingId.value === null) {
      const created = await recoveryApi.create(formValues)
      allRecoveries.value = [...allRecoveries.value, created]
    } else {
      const updated = await recoveryApi.update(editingId.value, formValues)
      allRecoveries.value = allRecoveries.value.map((item) =>
        item.id === updated.id ? updated : item,
      )
    }
    dialogVisible.value = false
  } catch {
    submitError.value = 'Could not save this recovery. Please try again.'
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

function methodLabel(method: ExtractionMethod): string {
  return method.extraction_protocol || `#${method.id}`
}

const newSetDialogVisible = ref(false)
const newSetName = ref('')
const savingSet = ref(false)

function openNewSetDialog() {
  newSetName.value = ''
  newSetDialogVisible.value = true
}

async function saveNewSet() {
  savingSet.value = true
  try {
    const created = await recoverySetApi.create({ name: newSetName.value || null })
    recoverySets.value = [...recoverySets.value, created]
    recoverySetId.value = created.id
    newSetDialogVisible.value = false
  } finally {
    savingSet.value = false
  }
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

    <div v-for="group in groupedRecoveries" :key="group.recoverySetId ?? 'ungrouped'" class="flex flex-col gap-2">
      <h4 class="font-medium text-sm">
        {{ group.recoverySet?.name ?? (group.recoverySetId === null ? 'Ungrouped' : `Set #${group.recoverySetId}`) }}
      </h4>
      <div class="overflow-x-auto">
        <DataTable :value="group.items" :loading="loading" data-key="id">
          <Column header="Surface">
            <template #body="{ data }">{{ data.surface ? surfaceLabel(data.surface) : '—' }}</template>
          </Column>
          <Column header="Sampling method">
            <template #body="{ data }">{{ data.sampling_method ? `#${data.sampling_method.id}` : '—' }}</template>
          </Column>
          <Column header="Extraction method">
            <template #body="{ data }">{{ data.extraction_method ? methodLabel(data.extraction_method) : '—' }}</template>
          </Column>
          <Column field="elution_volume" header="Elution volume" />
          <Column field="area" header="Area" />
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
      :ui="{ content: 'max-w-lg' }"
    >
      <template #body>
        <div class="flex flex-col gap-4">
          <div class="flex flex-col gap-2">
            <EntitySelect
              v-model="surfaceId"
              label="Surface"
              :options="studySurfaces"
              :option-label="surfaceLabel"
            />
            <UAlert
              v-if="errors.surface_id"
              color="error"
              variant="subtle"
              :description="errors.surface_id"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Recovery set (Optional)</label>
            <div class="flex gap-2">
              <EntitySelect
                v-model="recoverySetId"
                label=""
                :options="recoverySets"
                :option-label="(s: RecoverySet) => s.name || `Set #${s.id}`"
                class="flex-1"
              />
              <UButton icon="i-lucide-plus" variant="ghost" aria-label="Add recovery set" @click="openNewSetDialog" />
            </div>
          </div>
          <EntitySelect
            v-model="samplingMethodId"
            label="Sampling method"
            :options="samplingMethods"
            :option-label="(m: SamplingMethod) => `#${m.id}`"
          />
          <EntitySelect
            v-model="extractionMethodId"
            label="Extraction method"
            :options="extractionMethods"
            :option-label="methodLabel"
          />
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Elution volume</label>
            <UInputNumber
              v-model="elutionVolume"
              :color="errors.elution_volume ? 'error' : undefined"
              class="w-full"
            />
            <UAlert
              v-if="errors.elution_volume"
              color="error"
              variant="subtle"
              :description="errors.elution_volume"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Area</label>
            <UInputNumber
              v-model="area"
              :color="errors.area ? 'error' : undefined"
              class="w-full"
            />
            <UAlert
              v-if="errors.area"
              color="error"
              variant="subtle"
              :description="errors.area"
            />
          </div>
          <CategorySelect
            v-model="experienceLevelOfSamplerId"
            label="Experience level of sampler"
            :api="experienceLevelCategoryApi"
          />

          <UAlert v-if="submitError" color="error" variant="outline" :description="submitError" />
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" variant="ghost" @click="dialogVisible = false" />
        <UButton label="Save" :loading="submitting" @click="submitForm" />
      </template>
    </UModal>

    <UModal
      v-model:open="newSetDialogVisible"
      title="Add recovery set"
      :ui="{ content: 'max-w-sm' }"
    >
      <template #body>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Name</label>
          <UInput v-model="newSetName" class="w-full" autofocus />
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" variant="ghost" @click="newSetDialogVisible = false" />
        <UButton label="Add" :loading="savingSet" @click="saveNewSet" />
      </template>
    </UModal>
  </div>
</template>
