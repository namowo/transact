<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import Message from 'primevue/message'
import CategorySelect from '@/components/scenarios/CategorySelect.vue'
import EntitySelect from '@/components/scenarios/EntitySelect.vue'
import { recoveryApi, samplingMethodApi, extractionMethodApi } from '@/api/methods'
import { experienceLevelCategoryApi } from '@/api/categories'
import type { Contact, Recovery, RecoveryInput, SamplingMethod, ExtractionMethod, Surface } from '@/api/types'

const props = defineProps<{ contacts: Contact[] }>()

const emit = defineEmits<{
  'update:recoveries': [recoveries: Recovery[]]
}>()

function surfaceLabel(surface: Surface): string {
  const subject = surface.individual ? 'Individual' : (surface.item?.item_category?.name ?? 'Item')
  const part =
    surface.location_of_body_category?.name ?? surface.item_parts_category?.name ?? null
  return [subject, part].filter(Boolean).join(' — ') || `Surface #${surface.id}`
}

const scenarioSurfaces = computed<Surface[]>(() => {
  const bySurfaceId = new Map<number, Surface>()
  for (const contact of props.contacts) {
    if (contact.donor_surface) bySurfaceId.set(contact.donor_surface.id, contact.donor_surface)
    if (contact.recipient_surface)
      bySurfaceId.set(contact.recipient_surface.id, contact.recipient_surface)
  }
  return Array.from(bySurfaceId.values())
})

const scenarioSurfaceIds = computed(() => new Set(scenarioSurfaces.value.map((s) => s.id)))

const allRecoveries = ref<Recovery[]>([])
const loading = ref(false)
const loadError = ref('')

const recoveries = computed(() =>
  allRecoveries.value.filter(
    (recovery) => recovery.surface_id != null && scenarioSurfaceIds.value.has(recovery.surface_id),
  ),
)

watch(recoveries, (value) => emit('update:recoveries', value), { immediate: true })

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    allRecoveries.value = await recoveryApi.list()
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
    surface_id: null,
    sampling_method_id: null,
    extraction_method_id: null,
    elution_volume: null,
    area: null,
    experience_level_of_sampler_id: null,
  }
}

const schema = yup.object({
  surface_id: yup.number().nullable().required('Please select a surface.'),
  sampling_method_id: yup.number().nullable().defined(),
  extraction_method_id: yup.number().nullable().defined(),
  elution_volume: yup.number().nullable().min(0, 'Elution volume must be zero or greater.'),
  area: yup.number().nullable().min(0, 'Area must be zero or greater.'),
  experience_level_of_sampler_id: yup.number().nullable().defined(),
})

const { defineField, errors, handleSubmit, resetForm } = useForm<RecoveryInput>({
  validationSchema: schema,
  initialValues: emptyForm(),
})

const [surfaceId] = defineField('surface_id')
const [samplingMethodId] = defineField('sampling_method_id')
const [extractionMethodId] = defineField('extraction_method_id')
const [elutionVolume] = defineField('elution_volume')
const [area] = defineField('area')
const [experienceLevelOfSamplerId] = defineField('experience_level_of_sampler_id')

const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
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
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-between">
      <p class="text-sm text-surface-500 dark:text-surface-400">
        Samples recovered from this scenario's surfaces.
      </p>
      <Button
        label="Add recovery"
        icon="pi pi-plus"
        :disabled="!scenarioSurfaces.length"
        @click="openCreateDialog"
      />
    </div>

    <Message v-if="!scenarioSurfaces.length" severity="info" size="small">
      Add a contact with a donor or recipient surface before recording recoveries.
    </Message>

    <Message v-if="loadError" severity="error" size="small">{{ loadError }}</Message>

    <div class="overflow-x-auto">
      <DataTable :value="recoveries" :loading="loading" data-key="id">
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
              <Button icon="pi pi-pencil" text rounded aria-label="Edit" @click="openEditDialog(data)" />
              <Button
                icon="pi pi-trash"
                text
                rounded
                severity="danger"
                aria-label="Delete"
                @click="deleteRow(data)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <Dialog
      v-model:visible="dialogVisible"
      :header="editingId === null ? 'Add recovery' : 'Edit recovery'"
      modal
      :style="{ width: '32rem' }"
    >
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <EntitySelect
            v-model="surfaceId"
            label="Surface"
            :options="scenarioSurfaces"
            :option-label="surfaceLabel"
          />
          <Message v-if="errors.surface_id" severity="error" size="small" variant="simple">
            {{ errors.surface_id }}
          </Message>
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
          <InputNumber v-model="elutionVolume" :invalid="!!errors.elution_volume" fluid />
          <Message v-if="errors.elution_volume" severity="error" size="small" variant="simple">
            {{ errors.elution_volume }}
          </Message>
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Area</label>
          <InputNumber v-model="area" :invalid="!!errors.area" fluid />
          <Message v-if="errors.area" severity="error" size="small" variant="simple">
            {{ errors.area }}
          </Message>
        </div>
        <CategorySelect
          v-model="experienceLevelOfSamplerId"
          label="Experience level of sampler"
          :api="experienceLevelCategoryApi"
        />

        <Message v-if="submitError" severity="error" size="small">{{ submitError }}</Message>
      </div>
      <template #footer>
        <Button label="Cancel" text @click="dialogVisible = false" />
        <Button label="Save" :loading="submitting" @click="submitForm" />
      </template>
    </Dialog>
  </div>
</template>
