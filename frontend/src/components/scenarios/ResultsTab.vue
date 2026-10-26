<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import ContextMenu from 'openvue/contextmenu'
import { FilterMatchMode } from '@openvue/core/api'
import type { MenuItem } from 'openvue/menuitem'
import type { StepperItem } from '@nuxt/ui'
import EntitySelect from '@/components/scenarios/EntitySelect.vue'
import NamedCategoryRadioGroup from '@/components/scenarios/NamedCategoryRadioGroup.vue'
import RecoveryPicker from '@/components/scenarios/RecoveryPicker.vue'
import { surfaceLabel } from '@/components/data/recoveryLabel'
import { useIndividualOptions } from '@/components/scenarios/individualOptions'
import {
  resultApi,
  quantificationMethodApi,
  pcrMethodApi,
  postPcrTreatmentMethodApi,
  ceMethodApi,
  epgAnalysisMethodApi,
  epgInterpretationMethodApi,
} from '@/api/methods'
import { degradationCategoryApi } from '@/api/categories'
import type {
  Recovery,
  Result,
  ResultInput,
  PCR,
  PCRInput,
  PCRContributorInput,
  QuantificationMethod,
  PCRMethod,
  PostPCRTreatmentMethod,
  CEMethod,
  EPGAnalysisMethod,
  EPGInterpretationMethod,
} from '@/api/types'

const props = defineProps<{ recoveries: Recovery[]; studyId: string }>()

const { individualOptions } = useIndividualOptions(props.studyId)

// Contributor picker options: known Individuals plus as many "UPn" (unknown
// person) placeholders as could ever be needed. Unknown persons aren't
// their own entity - just an auto-numbered label scoped to one PCR run.
const unknownPersonOptions = Array.from({ length: 10 }, (_, i) => ({
  id: `__up_${i + 1}`,
  label: `UP${i + 1}`,
  unknownLabel: `UP${i + 1}`,
}))
const contributorOptions = computed(() => [
  ...individualOptions.value.map((individual) => ({
    id: individual.id,
    label: individual.label,
    unknownLabel: null as string | null,
  })),
  ...unknownPersonOptions,
])

function contributorKey(contributor: PCRContributorInput): string | null {
  if (contributor.individual_id) return contributor.individual_id
  if (contributor.unknown_label) {
    return unknownPersonOptions.find((up) => up.unknownLabel === contributor.unknown_label)?.id ?? null
  }
  return null
}

function setContributorKey(contributor: PCRContributorInput, key: string | null) {
  const option = contributorOptions.value.find((candidate) => candidate.id === key)
  contributor.individual_id = option && !option.unknownLabel ? option.id : null
  contributor.unknown_label = option?.unknownLabel ?? null
}

function emptyContributor(): PCRContributorInput {
  return { individual_id: null, unknown_label: null, mixture_proportion: null }
}

// Keeps the contributors array in sync with no_of_contributors: growing it
// adds blank rows, shrinking it drops the extra ones from the end.
function syncContributors(contributors: PCRContributorInput[], count: number | null): PCRContributorInput[] {
  const target = count ?? 0
  const next = contributors.slice(0, target)
  while (next.length < target) next.push(emptyContributor())
  return next
}

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

const degradationIcons: Record<string, string> = {
  severe: 'i-lucide-signal-high',
  moderate: 'i-lucide-signal-medium',
  mild: 'i-lucide-signal-low',
  none: 'i-lucide-circle-x',
  'not applied': 'i-lucide-circle-help',
}

function recoveryLabel(recovery?: Recovery | null): string {
  return surfaceLabel(recovery?.surface)
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
  if ('kit' in method && method.kit?.name) return method.kit.name
  if ('pcr_kit' in method && method.pcr_kit?.name) return method.pcr_kit.name
  if ('ce_device' in method && method.ce_device?.name) return method.ce_device.name
  if ('genotyping_software' in method && method.genotyping_software?.name)
    return method.genotyping_software.name
  if ('determination_of_noc' in method && method.determination_of_noc)
    return method.determination_of_noc
  return `#${method.id}`
}

function initFilters() {
  return {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
  }
}

const filters = ref(initFilters())

function clearFilters() {
  filters.value = initFilters()
}

// -- PCR form --
// pcrs is full-replace on Result update, so adding/editing/deleting one PCR
// run sends the whole list back with that one entry changed. The same form
// instance also backs the first PCR run embedded in the create-result
// dialog (see submitForm below), so the whole picture - recovery, result
// fields, and the first PCR run's methods/metrics - can be entered in one
// sitting like before PCR runs were split into their own entity.

function emptyPcrForm(): PCRInput {
  return {
    pcr_method_id: null,
    sample_input_volume_in_pcr: null,
    dna_input_amount_in_pcr: null,
    post_pcr_treatment_method_id: null,
    ce_method_id: null,
    epg_analysis_method_id: null,
    epg_interpretation_method_id: null,
    no_of_contributors: null,
    total_rfu: null,
    total_no_of_alleles: null,
    contributors: [],
  }
}

const pcrSchema = yup.object({
  pcr_method_id: yup.string().nullable().defined(),
  sample_input_volume_in_pcr: yup
    .number()
    .nullable()
    .min(0, 'Sample input volume must be zero or greater.'),
  dna_input_amount_in_pcr: yup
    .number()
    .nullable()
    .min(0, 'DNA input amount must be zero or greater.'),
  post_pcr_treatment_method_id: yup.string().nullable().defined(),
  ce_method_id: yup.string().nullable().defined(),
  epg_analysis_method_id: yup.string().nullable().defined(),
  epg_interpretation_method_id: yup.string().nullable().defined(),
  no_of_contributors: yup
    .number()
    .nullable()
    .integer('No. of contributors must be a whole number.')
    .min(0, 'No. of contributors must be zero or greater.'),
  total_rfu: yup.number().nullable().min(0, 'Total RFU must be zero or greater.'),
  total_no_of_alleles: yup
    .number()
    .nullable()
    .integer('Total no. of alleles must be a whole number.')
    .min(0, 'Total no. of alleles must be zero or greater.'),
  contributors: yup
    .array()
    .of(
      yup.object({
        individual_id: yup.string().nullable().defined(),
        unknown_label: yup.string().nullable().defined(),
        mixture_proportion: yup
          .number()
          .nullable()
          .min(0, 'Mixture proportion must be between 0 and 1.')
          .max(1, 'Mixture proportion must be between 0 and 1.'),
      }),
    )
    .defined(),
})

const {
  values: pcrFormValues,
  defineField: definePcrField,
  errors: pcrErrors,
  handleSubmit: handlePcrSubmit,
  resetForm: resetPcrForm,
  setFieldValue: setPcrFieldValue,
} = useForm<PCRInput>({
  validationSchema: pcrSchema,
  initialValues: emptyPcrForm(),
})

const [pcrMethodId] = definePcrField('pcr_method_id')
const [postPcrTreatmentMethodId] = definePcrField('post_pcr_treatment_method_id')
const [ceMethodId] = definePcrField('ce_method_id')
const [epgAnalysisMethodId] = definePcrField('epg_analysis_method_id')
const [epgInterpretationMethodId] = definePcrField('epg_interpretation_method_id')
const [sampleInputVolumeInPcr] = definePcrField('sample_input_volume_in_pcr')
const [dnaInputAmountInPcr] = definePcrField('dna_input_amount_in_pcr')
const [noOfContributors] = definePcrField('no_of_contributors')
const [totalRfu] = definePcrField('total_rfu')
const [totalNoOfAlleles] = definePcrField('total_no_of_alleles')

// CE methods available for the currently-selected PCR method, falling back
// to the full list when none are linked yet (e.g. the lab hasn't set this
// up in Settings yet), so the dropdown is never left empty.
const ceMethodOptions = computed(() => {
  const matching = ceMethods.value.filter((method) => method.pcr_method_id === pcrMethodId.value)
  return matching.length ? matching : ceMethods.value
})

watch(noOfContributors, (count) => {
  setPcrFieldValue('contributors', syncContributors(pcrFormValues.contributors ?? [], count))
})

function isBlankContributor(contributor: PCRContributorInput): boolean {
  return Object.values(contributor).every((value) => value === null)
}

function isBlankPcr(pcr: PCRInput): boolean {
  return (
    Object.entries(pcr).every(([key, value]) => key === 'contributors' || value === null) &&
    (pcr.contributors ?? []).every(isBlankContributor)
  )
}

// -- Result dialog --

function emptyForm(): ResultInput {
  return {
    recovery_id: null,
    quantification_method_id: null,
    dna_concentration: null,
    degradation_category_id: null,
    inhibition_category_id: null,
  }
}

const schema = yup.object({
  recovery_id: yup.string().nullable().required('Please select a recovery.'),
  quantification_method_id: yup.string().nullable().defined(),
  dna_concentration: yup.number().nullable().min(0, 'DNA concentration must be zero or greater.'),
  degradation_category_id: yup.string().nullable().defined(),
  inhibition_category_id: yup.string().nullable().defined(),
})

const { defineField, errors, handleSubmit, resetForm } = useForm<ResultInput>({
  validationSchema: schema,
  initialValues: emptyForm(),
})

const [recoveryId] = defineField('recovery_id')
const [quantificationMethodId] = defineField('quantification_method_id')
const [dnaConcentration] = defineField('dna_concentration')
const [degradationCategoryId] = defineField('degradation_category_id')
const [inhibitionCategoryId] = defineField('inhibition_category_id')

const dialogVisible = ref(false)
const editingId = ref<string | null>(null)
const submitting = ref(false)
const submitError = ref('')

// Only the create flow has a second step (the optional first PCR run) -
// editing a result never shows the stepper, just its own fields.
const activeStep = ref('result')
const stepItems = computed<StepperItem[]>(() => [
  { value: 'result', title: 'Result', slot: 'result' },
  { value: 'pcr', title: 'First PCR run', slot: 'pcr' },
])

function openCreateDialog() {
  editingId.value = null
  resetForm({ values: emptyForm() })
  resetPcrForm({ values: emptyPcrForm() })
  submitError.value = ''
  activeStep.value = 'result'
  dialogVisible.value = true
}

function openEditDialog(row: Result) {
  editingId.value = row.id
  resetForm({
    values: {
      recovery_id: row.recovery_id ?? null,
      quantification_method_id: row.quantification_method_id ?? null,
      dna_concentration: row.dna_concentration ?? null,
      degradation_category_id: row.degradation_category_id ?? null,
      inhibition_category_id: row.inhibition_category_id ?? null,
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
      const firstPcr = pcrFormValues as PCRInput
      const payload = isBlankPcr(firstPcr) ? formValues : { ...formValues, pcrs: [firstPcr] }
      const created = await resultApi.create(payload)
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

const expandedRows = ref<Record<string, boolean>>({})

// -- Result row context menu --

const resultContextMenu = ref<InstanceType<typeof ContextMenu>>()
const contextMenuResult = ref<Result>()

const resultContextMenuItems = computed<MenuItem[]>(() => {
  const result = contextMenuResult.value
  if (!result) return []
  return [
    { label: 'Edit', icon: 'i-lucide-pencil', command: () => openEditDialog(result) },
    { label: 'Delete', icon: 'i-lucide-trash-2', command: () => deleteRow(result) },
  ]
})

function openResultContextMenu(event: Event, result: Result) {
  contextMenuResult.value = result
  resultContextMenu.value?.show(event)
}

// -- PCR dialog --
// Used for adding/editing/deleting PCR runs on an already-saved result
// (beyond the first one entered alongside the result itself).

const pcrDialogVisible = ref(false)
const pcrDialogResult = ref<Result | null>(null)
const editingPcrId = ref<string | null>(null)
const submittingPcr = ref(false)
const submitPcrError = ref('')

function pcrInputOf(pcr: PCR): PCRInput {
  return {
    pcr_method_id: pcr.pcr_method_id ?? null,
    sample_input_volume_in_pcr: pcr.sample_input_volume_in_pcr ?? null,
    dna_input_amount_in_pcr: pcr.dna_input_amount_in_pcr ?? null,
    post_pcr_treatment_method_id: pcr.post_pcr_treatment_method_id ?? null,
    ce_method_id: pcr.ce_method_id ?? null,
    epg_analysis_method_id: pcr.epg_analysis_method_id ?? null,
    epg_interpretation_method_id: pcr.epg_interpretation_method_id ?? null,
    no_of_contributors: pcr.no_of_contributors ?? null,
    total_rfu: pcr.total_rfu ?? null,
    total_no_of_alleles: pcr.total_no_of_alleles ?? null,
    contributors: (pcr.contributors ?? []).map((contributor) => ({
      individual_id: contributor.individual_id ?? null,
      unknown_label: contributor.unknown_label ?? null,
      mixture_proportion: contributor.mixture_proportion ?? null,
    })),
  }
}

function openCreatePcrDialog(result: Result) {
  pcrDialogResult.value = result
  editingPcrId.value = null
  resetPcrForm({ values: emptyPcrForm() })
  submitPcrError.value = ''
  pcrDialogVisible.value = true
}

function openEditPcrDialog(result: Result, pcr: PCR) {
  pcrDialogResult.value = result
  editingPcrId.value = pcr.id
  resetPcrForm({ values: pcrInputOf(pcr) })
  submitPcrError.value = ''
  pcrDialogVisible.value = true
}

const submitPcrForm = handlePcrSubmit(async (formValues) => {
  const result = pcrDialogResult.value
  if (!result) return
  submittingPcr.value = true
  submitPcrError.value = ''
  try {
    const nextPcrs =
      editingPcrId.value === null
        ? [...result.pcrs.map(pcrInputOf), formValues]
        : result.pcrs.map((pcr) => (pcr.id === editingPcrId.value ? formValues : pcrInputOf(pcr)))
    const updated = await resultApi.update(result.id, { ...resultInputOf(result), pcrs: nextPcrs })
    allResults.value = allResults.value.map((item) => (item.id === updated.id ? updated : item))
    pcrDialogVisible.value = false
  } catch {
    submitPcrError.value = 'Could not save this PCR run. Please try again.'
  } finally {
    submittingPcr.value = false
  }
})

function resultInputOf(result: Result): ResultInput {
  return {
    recovery_id: result.recovery_id ?? null,
    quantification_method_id: result.quantification_method_id ?? null,
    dna_concentration: result.dna_concentration ?? null,
    degradation_category_id: result.degradation_category_id ?? null,
    inhibition_category_id: result.inhibition_category_id ?? null,
  }
}

async function deletePcr(result: Result, pcr: PCR) {
  if (!window.confirm('Delete this PCR run? This cannot be undone.')) return
  try {
    const nextPcrs = result.pcrs.filter((p) => p.id !== pcr.id).map(pcrInputOf)
    const updated = await resultApi.update(result.id, { ...resultInputOf(result), pcrs: nextPcrs })
    allResults.value = allResults.value.map((item) => (item.id === updated.id ? updated : item))
  } catch {
    loadError.value = 'Could not delete this PCR run. Please try again.'
  }
}

// -- PCR row context menu --

const pcrContextMenu = ref<InstanceType<typeof ContextMenu>>()
const contextMenuPcr = ref<{ result: Result; pcr: PCR }>()

const pcrContextMenuItems = computed<MenuItem[]>(() => {
  const entry = contextMenuPcr.value
  if (!entry) return []
  return [
    { label: 'Edit', icon: 'i-lucide-pencil', command: () => openEditPcrDialog(entry.result, entry.pcr) },
    { label: 'Delete', icon: 'i-lucide-trash-2', command: () => deletePcr(entry.result, entry.pcr) },
  ]
})

function openPcrContextMenu(event: Event, result: Result, pcr: PCR) {
  contextMenuPcr.value = { result, pcr }
  pcrContextMenu.value?.show(event)
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-between">
      <p class="text-sm text-surface-500 dark:text-surface-400">
        Lab results derived from this scenario's recoveries.
      </p>
      <UButton
        label="Add quantification result"
        icon="i-lucide-plus"
        variant="outline"
        :disabled="!recoveries.length"
        @click="openCreateDialog"
      />
    </div>

    <UAlert
      v-if="!recoveries.length"
      color="info"
      variant="outline"
      description="Add a recovery before recording results."
    />

    <UAlert v-if="loadError" color="error" variant="outline" :description="loadError" />

    <div class="overflow-x-auto">
      <div class="mb-3 flex items-center justify-between gap-3">
        <UButton type="button" icon="i-lucide-filter-x" variant="outline" size="sm" @click="clearFilters()">
          Clear Filters
        </UButton>
        <UInput
          v-model="(filters['global'] as { value: string | null }).value"
          type="text"
          icon="i-lucide-search"
          placeholder="Keyword Search"
        />
      </div>

      <ContextMenu ref="resultContextMenu" :model="resultContextMenuItems" />

      <DataTable
        v-model:filters="filters"
        v-model:expanded-rows="expandedRows"
        :value="results"
        :loading="loading"
        data-key="id"
        filterDisplay="menu"
        removableSort
        :globalFilterFields="['recovery.surface.id', 'dna_concentration']"
        @row-contextmenu="({ originalEvent, data }: { originalEvent: Event; data: Result }) => openResultContextMenu(originalEvent, data)"
      >
        <template #empty>No results recorded yet.</template>
        <Column expander style="width: 2.5rem" />
        <Column header="Recovery">
          <template #body="{ data }">{{ recoveryLabel(data.recovery) }}</template>
        </Column>
        <Column
          field="dna_concentration"
          header="DNA concentration"
          sortable
        >
          <template #body="{ data }">
            {{ data.dna_concentration != null ? `${data.dna_concentration.toFixed(4)} ng/µL` : '—' }}
          </template>
        </Column>
        <Column header="DNA quantity">
          <template #body="{ data }">
            {{ data.dna_quantity != null ? `${data.dna_quantity.toFixed(4)} ng` : '—' }}
          </template>
        </Column>
        <Column header="Degradation Index">
          <template #body="{ data }">{{ data.degradation_category?.name ?? '—' }}</template>
        </Column>
        <Column header="Genotyping results" style="width: 8rem">
          <template #body="{ data }">{{ data.pcrs.length }}</template>
        </Column>
        <Column header="" style="width: 3rem">
          <template #body="{ data }">
            <UButton
              icon="i-lucide-more-vertical"
              color="neutral"
              variant="ghost"
              square
              aria-label="Result options"
              @click.stop="openResultContextMenu($event, data)"
            />
          </template>
        </Column>

        <template #expansion="{ data: result }">
          <div class="flex flex-col gap-2 p-2">
            <div class="flex items-center justify-between">
              <h5 class="font-medium text-sm">Genotyping results</h5>
              <UButton
                label="Add genotyping result"
                icon="i-lucide-plus"
                variant="outline"
                size="sm"
                @click="openCreatePcrDialog(result)"
              />
            </div>
            <ContextMenu ref="pcrContextMenu" :model="pcrContextMenuItems" />
            <DataTable
              :value="result.pcrs"
              data-key="id"
              @row-contextmenu="({ originalEvent, data }: { originalEvent: Event; data: PCR }) => openPcrContextMenu(originalEvent, result, data)"
            >
              <template #empty>No genotyping results recorded yet.</template>
              <Column header="PCR method">
                <template #body="{ data }">{{ data.pcr_method ? methodLabel(data.pcr_method) : '—' }}</template>
              </Column>
              <Column header="No. of contributors">
                <template #body="{ data }">{{ data.no_of_contributors ?? '—' }}</template>
              </Column>
              <Column header="Total RFU">
                <template #body="{ data }">
                  {{ data.total_rfu != null ? `${data.total_rfu} RFU` : '—' }}
                </template>
              </Column>
              <Column header="" style="width: 3rem">
                <template #body="{ data }">
                  <UButton
                    icon="i-lucide-more-vertical"
                    color="neutral"
                    variant="ghost"
                    square
                    aria-label="Genotyping result options"
                    @click.stop="openPcrContextMenu($event, result, data)"
                  />
                </template>
              </Column>
            </DataTable>
          </div>
        </template>
      </DataTable>
    </div>

    <UModal
      v-model:open="dialogVisible"
      :title="editingId === null ? 'Add quantification result' : 'Edit quantification result'"
      :ui="{ content: 'max-w-xl', footer: 'justify-end' }"
    >
      <template #body>
        <div v-if="editingId !== null" class="flex flex-col gap-4">
          <RecoveryPicker v-model="recoveryId" :recoveries="recoveries" :error="errors.recovery_id" />

          <EntitySelect
            v-model="quantificationMethodId"
            label="Quantification method"
            :options="quantificationMethods"
            :option-label="methodLabel"
          />
          <p v-if="!quantificationMethods.length" class="text-sm text-surface-500 dark:text-surface-400 -mt-2">
            No quantification methods yet. Add one under
            <RouterLink :to="{ name: 'settings-methods-quantification' }" class="underline" target="_blank">
              Settings → Methods → Quantification
            </RouterLink>.
          </p>

          <UFormField label="DNA concentration" :error="errors.dna_concentration">
            <UFieldGroup>
              <UInputNumber v-model="dnaConcentration" :step="0.0001" orientation="vertical" class="w-full" />
              <UBadge color="neutral" variant="outline" size="lg" label="ng/µL" />
            </UFieldGroup>
          </UFormField>
          <NamedCategoryRadioGroup
            v-model="degradationCategoryId"
            label="Degradation Index"
            :api="degradationCategoryApi"
            :icons="degradationIcons"
            variant="table"
            orientation="horizontal"
          />

          <UAlert v-if="submitError" color="error" variant="outline" :description="submitError" />
        </div>

        <UStepper
          v-else
          v-model="activeStep"
          :items="stepItems"
          :linear="false"
          class="bg-transparent!"
        >
          <template #result>
            <div class="flex flex-col gap-4">
              <RecoveryPicker v-model="recoveryId" :recoveries="recoveries" :error="errors.recovery_id" />

              <EntitySelect
                v-model="quantificationMethodId"
                label="Quantification method"
                :options="quantificationMethods"
                :option-label="methodLabel"
              />
              <p v-if="!quantificationMethods.length" class="text-sm text-surface-500 dark:text-surface-400 -mt-2">
                No quantification methods yet. Add one under
                <RouterLink :to="{ name: 'settings-methods-quantification' }" class="underline" target="_blank">
                  Settings → Methods → Quantification
                </RouterLink>.
              </p>

              <UFormField label="DNA concentration" :error="errors.dna_concentration">
                <UFieldGroup>
                  <UInputNumber v-model="dnaConcentration" :step="0.0001" orientation="vertical" class="w-full" />
                  <UBadge color="neutral" variant="outline" size="lg" label="ng/µL" />
                </UFieldGroup>
              </UFormField>
              <NamedCategoryRadioGroup
                v-model="degradationCategoryId"
                label="Degradation Index"
                :api="degradationCategoryApi"
                :icons="degradationIcons"
                variant="table"
                orientation="horizontal"
              />
              <div class="flex justify-end mt-2">
                <UButton
                  label="Continue"
                  trailing-icon="i-lucide-arrow-right"
                  variant="outline"
                  @click="activeStep = 'pcr'"
                />
              </div>
            </div>
          </template>

          <template #pcr>
            <div class="flex flex-col gap-4">
              <p class="text-sm text-surface-500 dark:text-surface-400">
                The first genotyping result for this quantification result.
              </p>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="flex flex-col gap-1">
                  <EntitySelect
                    v-model="pcrMethodId"
                    label="PCR method"
                    :options="pcrMethods"
                    :option-label="methodLabel"
                  />
                  <p v-if="!pcrMethods.length" class="text-sm text-surface-500 dark:text-surface-400">
                    No PCR methods yet. Add one under
                    <RouterLink :to="{ name: 'settings-methods-pcr' }" class="underline" target="_blank">
                      Settings → Methods → PCR
                    </RouterLink>.
                  </p>
                </div>
                <div class="flex flex-col gap-1">
                  <EntitySelect
                    v-model="postPcrTreatmentMethodId"
                    label="Post-PCR treatment method"
                    :options="postPcrTreatmentMethods"
                    :option-label="(m: PostPCRTreatmentMethod) => `#${m.id}`"
                  />
                  <p v-if="!postPcrTreatmentMethods.length" class="text-sm text-surface-500 dark:text-surface-400">
                    No post-PCR treatment methods yet. Add one under
                    <RouterLink :to="{ name: 'settings-methods-post-pcr-treatment' }" class="underline" target="_blank">
                      Settings → Methods → Post-PCR treatment
                    </RouterLink>.
                  </p>
                </div>
                <div class="flex flex-col gap-1">
                  <EntitySelect
                    v-model="ceMethodId"
                    label="CE method"
                    :options="ceMethodOptions"
                    :option-label="methodLabel"
                  />
                  <p v-if="!ceMethods.length" class="text-sm text-surface-500 dark:text-surface-400">
                    No CE methods yet. Add one under
                    <RouterLink :to="{ name: 'settings-methods-ce' }" class="underline" target="_blank">
                      Settings → Methods → CE
                    </RouterLink>.
                  </p>
                </div>
                <div class="flex flex-col gap-1">
                  <EntitySelect
                    v-model="epgAnalysisMethodId"
                    label="EPG analysis method"
                    :options="epgAnalysisMethods"
                    :option-label="methodLabel"
                  />
                  <p v-if="!epgAnalysisMethods.length" class="text-sm text-surface-500 dark:text-surface-400">
                    No EPG analysis methods yet. Add one under
                    <RouterLink :to="{ name: 'settings-methods-epg-analysis' }" class="underline" target="_blank">
                      Settings → Methods → EPG analysis
                    </RouterLink>.
                  </p>
                </div>
                <div class="flex flex-col gap-1">
                  <EntitySelect
                    v-model="epgInterpretationMethodId"
                    label="EPG interpretation method"
                    :options="epgInterpretationMethods"
                    :option-label="methodLabel"
                  />
                  <p v-if="!epgInterpretationMethods.length" class="text-sm text-surface-500 dark:text-surface-400">
                    No EPG interpretation methods yet. Add one under
                    <RouterLink :to="{ name: 'settings-methods-epg-interpretation' }" class="underline" target="_blank">
                      Settings → Methods → EPG interpretation
                    </RouterLink>.
                  </p>
                </div>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <UFormField label="Sample input volume in PCR" :error="pcrErrors.sample_input_volume_in_pcr">
                  <UFieldGroup>
                    <UInputNumber v-model="sampleInputVolumeInPcr" :step="0.1" orientation="vertical" class="w-full" />
                    <UBadge color="neutral" variant="outline" size="lg" label="µL" />
                  </UFieldGroup>
                </UFormField>
                <UFormField label="DNA input amount in PCR" :error="pcrErrors.dna_input_amount_in_pcr">
                  <UFieldGroup>
                    <UInputNumber v-model="dnaInputAmountInPcr" :step="0.001" orientation="vertical" class="w-full" />
                    <UBadge color="neutral" variant="outline" size="lg" label="pg" />
                  </UFieldGroup>
                </UFormField>
                <UFormField label="No. of contributors" :error="pcrErrors.no_of_contributors">
                  <UInputNumber v-model="noOfContributors" :min="0" orientation="vertical" class="w-full" />
                </UFormField>
                <UFormField label="Total RFU" :error="pcrErrors.total_rfu">
                  <UFieldGroup>
                    <UInputNumber v-model="totalRfu" orientation="vertical" class="w-full" />
                    <UBadge color="neutral" variant="outline" size="lg" label="RFU" />
                  </UFieldGroup>
                </UFormField>
                <UFormField label="Total no. of alleles" :error="pcrErrors.total_no_of_alleles">
                  <UInputNumber v-model="totalNoOfAlleles" orientation="vertical" class="w-full" />
                </UFormField>
              </div>

              <div v-if="pcrFormValues.contributors?.length" class="flex flex-col gap-2">
                <label class="font-medium text-sm">Mixture proportions</label>
                <div
                  v-for="(contributor, index) in pcrFormValues.contributors"
                  :key="index"
                  class="flex items-end gap-2"
                >
                  <UFormField :label="`Contributor ${index + 1}`" class="flex-1">
                    <USelectMenu
                      :model-value="contributorKey(contributor)"
                      :items="contributorOptions"
                      value-key="id"
                      placeholder="Select an individual or unknown person"
                      clear
                      class="w-full"
                      @update:model-value="setContributorKey(contributor, $event)"
                    />
                  </UFormField>
                  <UFormField label="Mx" class="w-28">
                    <UInputNumber
                      v-model="contributor.mixture_proportion"
                      :min="0"
                      :max="1"
                      :step="0.01"
                      orientation="vertical"
                      class="w-full"
                    />
                  </UFormField>
                </div>
              </div>

              <div class="flex justify-start mt-2">
                <UButton
                  label="Back"
                  icon="i-lucide-arrow-left"
                  variant="ghost"
                  @click="activeStep = 'result'"
                />
              </div>

              <UAlert v-if="submitError" color="error" variant="outline" :description="submitError" />
            </div>
          </template>
        </UStepper>
      </template>
      <template #footer>
        <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="dialogVisible = false" />
        <UButton label="Save" icon="i-lucide-save" :loading="submitting" @click="submitForm" />
      </template>
    </UModal>

    <UModal
      v-model:open="pcrDialogVisible"
      :title="editingPcrId === null ? 'Add genotyping result' : 'Edit genotyping result'"
      :ui="{ content: 'max-w-xl', footer: 'justify-end' }"
    >
      <template #body>
        <div class="flex flex-col gap-4">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="flex flex-col gap-1">
              <EntitySelect
                v-model="pcrMethodId"
                label="PCR method"
                :options="pcrMethods"
                :option-label="methodLabel"
              />
              <p v-if="!pcrMethods.length" class="text-sm text-surface-500 dark:text-surface-400">
                No PCR methods yet. Add one under
                <RouterLink :to="{ name: 'settings-methods-pcr' }" class="underline" target="_blank">
                  Settings → Methods → PCR
                </RouterLink>.
              </p>
            </div>
            <div class="flex flex-col gap-1">
              <EntitySelect
                v-model="postPcrTreatmentMethodId"
                label="Post-PCR treatment method"
                :options="postPcrTreatmentMethods"
                :option-label="(m: PostPCRTreatmentMethod) => `#${m.id}`"
              />
              <p v-if="!postPcrTreatmentMethods.length" class="text-sm text-surface-500 dark:text-surface-400">
                No post-PCR treatment methods yet. Add one under
                <RouterLink :to="{ name: 'settings-methods-post-pcr-treatment' }" class="underline" target="_blank">
                  Settings → Methods → Post-PCR treatment
                </RouterLink>.
              </p>
            </div>
            <div class="flex flex-col gap-1">
              <EntitySelect
                v-model="ceMethodId"
                label="CE method"
                :options="ceMethodOptions"
                :option-label="methodLabel"
              />
              <p v-if="!ceMethods.length" class="text-sm text-surface-500 dark:text-surface-400">
                No CE methods yet. Add one under
                <RouterLink :to="{ name: 'settings-methods-ce' }" class="underline" target="_blank">
                  Settings → Methods → CE
                </RouterLink>.
              </p>
            </div>
            <div class="flex flex-col gap-1">
              <EntitySelect
                v-model="epgAnalysisMethodId"
                label="EPG analysis method"
                :options="epgAnalysisMethods"
                :option-label="methodLabel"
              />
              <p v-if="!epgAnalysisMethods.length" class="text-sm text-surface-500 dark:text-surface-400">
                No EPG analysis methods yet. Add one under
                <RouterLink :to="{ name: 'settings-methods-epg-analysis' }" class="underline" target="_blank">
                  Settings → Methods → EPG analysis
                </RouterLink>.
              </p>
            </div>
            <div class="flex flex-col gap-1">
              <EntitySelect
                v-model="epgInterpretationMethodId"
                label="EPG interpretation method"
                :options="epgInterpretationMethods"
                :option-label="methodLabel"
              />
              <p v-if="!epgInterpretationMethods.length" class="text-sm text-surface-500 dark:text-surface-400">
                No EPG interpretation methods yet. Add one under
                <RouterLink :to="{ name: 'settings-methods-epg-interpretation' }" class="underline" target="_blank">
                  Settings → Methods → EPG interpretation
                </RouterLink>.
              </p>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <UFormField label="Sample input volume in PCR" :error="pcrErrors.sample_input_volume_in_pcr">
              <UFieldGroup>
                <UInputNumber v-model="sampleInputVolumeInPcr" :step="0.1" orientation="vertical" class="w-full" />
                <UBadge color="neutral" variant="outline" size="lg" label="µL" />
              </UFieldGroup>
            </UFormField>
            <UFormField label="DNA input amount in PCR" :error="pcrErrors.dna_input_amount_in_pcr">
              <UFieldGroup>
                <UInputNumber v-model="dnaInputAmountInPcr" :step="0.001" orientation="vertical" class="w-full" />
                <UBadge color="neutral" variant="outline" size="lg" label="pg" />
              </UFieldGroup>
            </UFormField>
            <UFormField label="No. of contributors" :error="pcrErrors.no_of_contributors">
              <UInputNumber v-model="noOfContributors" :min="0" orientation="vertical" class="w-full" />
            </UFormField>
            <UFormField label="Total RFU" :error="pcrErrors.total_rfu">
              <UFieldGroup>
                <UInputNumber v-model="totalRfu" orientation="vertical" class="w-full" />
                <UBadge color="neutral" variant="outline" size="lg" label="RFU" />
              </UFieldGroup>
            </UFormField>
            <UFormField label="Total no. of alleles" :error="pcrErrors.total_no_of_alleles">
              <UInputNumber v-model="totalNoOfAlleles" orientation="vertical" class="w-full" />
            </UFormField>
          </div>

          <div v-if="pcrFormValues.contributors?.length" class="flex flex-col gap-2">
            <label class="font-medium text-sm">Mixture proportions</label>
            <div
              v-for="(contributor, index) in pcrFormValues.contributors"
              :key="index"
              class="flex items-end gap-2"
            >
              <UFormField :label="`Contributor ${index + 1}`" class="flex-1">
                <USelectMenu
                  :model-value="contributorKey(contributor)"
                  :items="contributorOptions"
                  value-key="id"
                  placeholder="Select an individual or unknown person"
                  clear
                  class="w-full"
                  @update:model-value="setContributorKey(contributor, $event)"
                />
              </UFormField>
              <UFormField label="Mx" class="w-28">
                <UInputNumber
                  v-model="contributor.mixture_proportion"
                  :min="0"
                  :max="1"
                  :step="0.01"
                  orientation="vertical"
                  class="w-full"
                />
              </UFormField>
            </div>
          </div>

          <UAlert v-if="submitPcrError" color="error" variant="outline" :description="submitPcrError" />
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="pcrDialogVisible = false" />
        <UButton label="Save" icon="i-lucide-save" :loading="submittingPcr" @click="submitPcrForm" />
      </template>
    </UModal>
  </div>
</template>
