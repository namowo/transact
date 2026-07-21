<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import ToggleSwitch from 'primevue/toggleswitch'
import Message from 'primevue/message'
import EntitySelect from '@/components/scenarios/EntitySelect.vue'
import {
  resultApi,
  quantificationMethodApi,
  pcrMethodApi,
  postPcrTreatmentMethodApi,
  ceMethodApi,
  epgAnalysisMethodApi,
  epgInterpretationMethodApi,
} from '@/api/methods'
import type {
  Recovery,
  Result,
  ResultInput,
  QuantificationMethod,
  PCRMethod,
  PostPCRTreatmentMethod,
  CEMethod,
  EPGAnalysisMethod,
  EPGInterpretationMethod,
} from '@/api/types'

const props = defineProps<{ recoveries: Recovery[] }>()

const recoveryIds = computed(() => new Set(props.recoveries.map((r) => r.id)))

const allResults = ref<Result[]>([])
const loading = ref(false)
const loadError = ref('')

const results = computed(() =>
  allResults.value.filter((result) => result.recovery_id != null && recoveryIds.value.has(result.recovery_id)),
)

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    allResults.value = await resultApi.list()
  } catch {
    loadError.value = 'Could not load results. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

const quantificationMethods = ref<QuantificationMethod[]>([])
const pcrMethods = ref<PCRMethod[]>([])
const postPcrTreatmentMethods = ref<PostPCRTreatmentMethod[]>([])
const ceMethods = ref<CEMethod[]>([])
const epgAnalysisMethods = ref<EPGAnalysisMethod[]>([])
const epgInterpretationMethods = ref<EPGInterpretationMethod[]>([])

onMounted(async () => {
  quantificationMethods.value = await quantificationMethodApi.list()
  pcrMethods.value = await pcrMethodApi.list()
  postPcrTreatmentMethods.value = await postPcrTreatmentMethodApi.list()
  ceMethods.value = await ceMethodApi.list()
  epgAnalysisMethods.value = await epgAnalysisMethodApi.list()
  epgInterpretationMethods.value = await epgInterpretationMethodApi.list()
})

function recoveryLabel(recovery: Recovery): string {
  return recovery.surface ? `Recovery #${recovery.id}` : `Recovery #${recovery.id}`
}

function methodLabel(
  method:
    | QuantificationMethod
    | PCRMethod
    | PostPCRTreatmentMethod
    | CEMethod
    | EPGAnalysisMethod
    | EPGInterpretationMethod,
): string {
  if ('kit' in method && method.kit) return method.kit
  if ('pcr_kit' in method && method.pcr_kit) return method.pcr_kit
  if ('ce_device' in method && method.ce_device) return method.ce_device
  if ('genotyping_software' in method && method.genotyping_software)
    return method.genotyping_software
  if ('determination_of_noc' in method && method.determination_of_noc)
    return method.determination_of_noc
  return `#${method.id}`
}

function emptyForm(): ResultInput {
  return {
    recovery_id: null,
    quantification_method_id: null,
    dna_concentration: null,
    degradation: null,
    inhibition: null,
    dna_quantity: null,
    pcr_method_id: null,
    sample_input_volume_in_pcr: null,
    dna_input_amount_in_pcr: null,
    post_pcr_treatment_method_id: null,
    ce_method_id: null,
    epg_analysis_method_id: null,
    epg_interpretation_method_id: null,
    no_of_contributors: null,
    mixture_proportion: null,
    total_rfu: null,
    total_no_of_alleles: null,
  }
}

const schema = yup.object({
  recovery_id: yup.number().nullable().required('Please select a recovery.'),
  quantification_method_id: yup.number().nullable().defined(),
  dna_concentration: yup.number().nullable().min(0, 'DNA concentration must be zero or greater.'),
  degradation: yup.string().nullable().defined(),
  inhibition: yup.boolean().nullable().defined(),
  dna_quantity: yup.number().nullable().min(0, 'DNA quantity must be zero or greater.'),
  pcr_method_id: yup.number().nullable().defined(),
  sample_input_volume_in_pcr: yup
    .number()
    .nullable()
    .min(0, 'Sample input volume must be zero or greater.'),
  dna_input_amount_in_pcr: yup
    .number()
    .nullable()
    .min(0, 'DNA input amount must be zero or greater.'),
  post_pcr_treatment_method_id: yup.number().nullable().defined(),
  ce_method_id: yup.number().nullable().defined(),
  epg_analysis_method_id: yup.number().nullable().defined(),
  epg_interpretation_method_id: yup.number().nullable().defined(),
  no_of_contributors: yup
    .number()
    .nullable()
    .integer('No. of contributors must be a whole number.')
    .min(0, 'No. of contributors must be zero or greater.'),
  mixture_proportion: yup
    .number()
    .nullable()
    .min(0, 'Mixture proportion must be between 0 and 1.')
    .max(1, 'Mixture proportion must be between 0 and 1.'),
  total_rfu: yup.number().nullable().min(0, 'Total RFU must be zero or greater.'),
  total_no_of_alleles: yup
    .number()
    .nullable()
    .integer('Total no. of alleles must be a whole number.')
    .min(0, 'Total no. of alleles must be zero or greater.'),
})

const { defineField, errors, handleSubmit, resetForm } = useForm<ResultInput>({
  validationSchema: schema,
  initialValues: emptyForm(),
})

const [recoveryId] = defineField('recovery_id')
const [quantificationMethodId] = defineField('quantification_method_id')
const [pcrMethodId] = defineField('pcr_method_id')
const [postPcrTreatmentMethodId] = defineField('post_pcr_treatment_method_id')
const [ceMethodId] = defineField('ce_method_id')
const [epgAnalysisMethodId] = defineField('epg_analysis_method_id')
const [epgInterpretationMethodId] = defineField('epg_interpretation_method_id')
const [dnaConcentration] = defineField('dna_concentration')
const [dnaQuantity] = defineField('dna_quantity')
const [degradation] = defineField('degradation')
const [inhibition] = defineField('inhibition')
const [sampleInputVolumeInPcr] = defineField('sample_input_volume_in_pcr')
const [dnaInputAmountInPcr] = defineField('dna_input_amount_in_pcr')
const [noOfContributors] = defineField('no_of_contributors')
const [mixtureProportion] = defineField('mixture_proportion')
const [totalRfu] = defineField('total_rfu')
const [totalNoOfAlleles] = defineField('total_no_of_alleles')

const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const submitting = ref(false)
const submitError = ref('')

// ToggleSwitch doesn't accept a nullable model, but inhibition is a
// genuinely optional boolean (untested vs. true/false), so translate at the
// binding boundary rather than losing the null state in ResultInput.
const inhibitionToggle = computed({
  get: () => inhibition.value ?? false,
  set: (value: boolean) => {
    inhibition.value = value
  },
})

function openCreateDialog() {
  editingId.value = null
  resetForm({ values: emptyForm() })
  submitError.value = ''
  dialogVisible.value = true
}

function openEditDialog(row: Result) {
  editingId.value = row.id
  resetForm({
    values: {
      recovery_id: row.recovery_id ?? null,
      quantification_method_id: row.quantification_method_id ?? null,
      dna_concentration: row.dna_concentration ?? null,
      degradation: row.degradation ?? null,
      inhibition: row.inhibition ?? null,
      dna_quantity: row.dna_quantity ?? null,
      pcr_method_id: row.pcr_method_id ?? null,
      sample_input_volume_in_pcr: row.sample_input_volume_in_pcr ?? null,
      dna_input_amount_in_pcr: row.dna_input_amount_in_pcr ?? null,
      post_pcr_treatment_method_id: row.post_pcr_treatment_method_id ?? null,
      ce_method_id: row.ce_method_id ?? null,
      epg_analysis_method_id: row.epg_analysis_method_id ?? null,
      epg_interpretation_method_id: row.epg_interpretation_method_id ?? null,
      no_of_contributors: row.no_of_contributors ?? null,
      mixture_proportion: row.mixture_proportion ?? null,
      total_rfu: row.total_rfu ?? null,
      total_no_of_alleles: row.total_no_of_alleles ?? null,
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
      const created = await resultApi.create(formValues)
      allResults.value = [...allResults.value, created]
    } else {
      const updated = await resultApi.update(editingId.value, formValues)
      allResults.value = allResults.value.map((item) => (item.id === updated.id ? updated : item))
    }
    dialogVisible.value = false
  } catch {
    submitError.value = 'Could not save this result. Please try again.'
  } finally {
    submitting.value = false
  }
})

async function deleteRow(row: Result) {
  if (!window.confirm('Delete this result? This cannot be undone.')) return
  try {
    await resultApi.delete(row.id)
    allResults.value = allResults.value.filter((item) => item.id !== row.id)
  } catch {
    loadError.value = 'Could not delete this result. Please try again.'
  }
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-between">
      <p class="text-sm text-surface-500 dark:text-surface-400">
        Lab results derived from this scenario's recoveries.
      </p>
      <Button
        label="Add result"
        icon="pi pi-plus"
        :disabled="!recoveries.length"
        @click="openCreateDialog"
      />
    </div>

    <Message v-if="!recoveries.length" severity="info" size="small">
      Add a recovery before recording results.
    </Message>

    <Message v-if="loadError" severity="error" size="small">{{ loadError }}</Message>

    <div class="overflow-x-auto">
      <DataTable :value="results" :loading="loading" data-key="id">
        <Column header="Recovery">
          <template #body="{ data }">{{ data.recovery ? recoveryLabel(data.recovery) : '—' }}</template>
        </Column>
        <Column field="dna_concentration" header="DNA concentration" />
        <Column field="dna_quantity" header="DNA quantity" />
        <Column field="no_of_contributors" header="No. of contributors" />
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
      :header="editingId === null ? 'Add result' : 'Edit result'"
      modal
      :style="{ width: '36rem' }"
    >
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <EntitySelect
            v-model="recoveryId"
            label="Recovery"
            :options="recoveries"
            :option-label="recoveryLabel"
          />
          <Message v-if="errors.recovery_id" severity="error" size="small" variant="simple">
            {{ errors.recovery_id }}
          </Message>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <EntitySelect
            v-model="quantificationMethodId"
            label="Quantification method"
            :options="quantificationMethods"
            :option-label="methodLabel"
          />
          <EntitySelect
            v-model="pcrMethodId"
            label="PCR method"
            :options="pcrMethods"
            :option-label="methodLabel"
          />
          <EntitySelect
            v-model="postPcrTreatmentMethodId"
            label="Post-PCR treatment method"
            :options="postPcrTreatmentMethods"
            :option-label="(m: PostPCRTreatmentMethod) => `#${m.id}`"
          />
          <EntitySelect
            v-model="ceMethodId"
            label="CE method"
            :options="ceMethods"
            :option-label="methodLabel"
          />
          <EntitySelect
            v-model="epgAnalysisMethodId"
            label="EPG analysis method"
            :options="epgAnalysisMethods"
            :option-label="methodLabel"
          />
          <EntitySelect
            v-model="epgInterpretationMethodId"
            label="EPG interpretation method"
            :options="epgInterpretationMethods"
            :option-label="methodLabel"
          />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">DNA concentration</label>
            <InputNumber v-model="dnaConcentration" :invalid="!!errors.dna_concentration" fluid />
            <Message v-if="errors.dna_concentration" severity="error" size="small" variant="simple">
              {{ errors.dna_concentration }}
            </Message>
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">DNA quantity</label>
            <InputNumber v-model="dnaQuantity" :invalid="!!errors.dna_quantity" fluid />
            <Message v-if="errors.dna_quantity" severity="error" size="small" variant="simple">
              {{ errors.dna_quantity }}
            </Message>
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Degradation</label>
            <InputText v-model="degradation" fluid />
          </div>
          <div class="flex items-center gap-2 pt-6">
            <ToggleSwitch v-model="inhibitionToggle" input-id="inhibition" />
            <label for="inhibition" class="text-sm">Inhibition</label>
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Sample input volume in PCR</label>
            <InputNumber
              v-model="sampleInputVolumeInPcr"
              :invalid="!!errors.sample_input_volume_in_pcr"
              fluid
            />
            <Message
              v-if="errors.sample_input_volume_in_pcr"
              severity="error"
              size="small"
              variant="simple"
            >
              {{ errors.sample_input_volume_in_pcr }}
            </Message>
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">DNA input amount in PCR</label>
            <InputNumber
              v-model="dnaInputAmountInPcr"
              :invalid="!!errors.dna_input_amount_in_pcr"
              fluid
            />
            <Message
              v-if="errors.dna_input_amount_in_pcr"
              severity="error"
              size="small"
              variant="simple"
            >
              {{ errors.dna_input_amount_in_pcr }}
            </Message>
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">No. of contributors</label>
            <InputNumber v-model="noOfContributors" :invalid="!!errors.no_of_contributors" fluid />
            <Message v-if="errors.no_of_contributors" severity="error" size="small" variant="simple">
              {{ errors.no_of_contributors }}
            </Message>
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Mixture proportion</label>
            <InputNumber v-model="mixtureProportion" :invalid="!!errors.mixture_proportion" fluid />
            <Message v-if="errors.mixture_proportion" severity="error" size="small" variant="simple">
              {{ errors.mixture_proportion }}
            </Message>
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Total RFU</label>
            <InputNumber v-model="totalRfu" :invalid="!!errors.total_rfu" fluid />
            <Message v-if="errors.total_rfu" severity="error" size="small" variant="simple">
              {{ errors.total_rfu }}
            </Message>
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Total no. of alleles</label>
            <InputNumber
              v-model="totalNoOfAlleles"
              :invalid="!!errors.total_no_of_alleles"
              fluid
            />
            <Message
              v-if="errors.total_no_of_alleles"
              severity="error"
              size="small"
              variant="simple"
            >
              {{ errors.total_no_of_alleles }}
            </Message>
          </div>
        </div>

        <Message v-if="submitError" severity="error" size="small">{{ submitError }}</Message>
      </div>
      <template #footer>
        <Button label="Cancel" text @click="dialogVisible = false" />
        <Button label="Save" :loading="submitting" @click="submitForm" />
      </template>
    </Dialog>
  </div>
</template>
