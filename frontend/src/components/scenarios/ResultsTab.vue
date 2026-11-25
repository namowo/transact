<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import type { ContextMenuItem, StepperItem, TableColumn, TableRow } from '@nuxt/ui'
import EntitySelect from '@/components/scenarios/EntitySelect.vue'
import SamplePicker from '@/components/scenarios/SamplePicker.vue'
import { surfaceLabel } from '@/components/data/sampleLabel'
import ScenarioBadges from '@/components/data/ScenarioBadges.vue'
import { useAuthStore } from '@/stores/auth'
import { useStudyReadOnly } from '@/composables/useStudyAccess'
import CsvRoundTrip from '@/components/data/CsvRoundTrip.vue'
import { sortRows, useTableSort } from '@/composables/useTableSort'
import TableSortHint from '@/components/data/TableSortHint.vue'
import { parseNumber, type DecimalSeparator } from '@/components/data/csv'
import { useToast } from '@nuxt/ui/composables'
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
import { ceMethodLabels } from '@/data/labMethods'
import type {
  Contact,
  Sample,
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
import { manualSorting, useTableView } from '@/composables/useTableView'
import { expandColumn, sortHeader } from '@/composables/tableColumns'
import TableFilterDrawer from '@/components/ui/TableFilterDrawer.vue'
import TablePagination from '@/components/ui/TablePagination.vue'

const props = defineProps<{
  samples: Sample[]
  studyId: string
  surfaceScenarios: Record<string, string[]>
  contacts?: Contact[]
  exportName?: string
}>()

const auth = useAuthStore()
const readOnly = useStudyReadOnly()
const FIXED4 = { minimumFractionDigits: 4, maximumFractionDigits: 4 }
const toast = useToast()

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

// Only individuals that took part in the sample's contact can have left the
// DNA (its donor and recipient); unknown persons stay selectable. Individuals
// already chosen on a row stay listed so existing data never disappears.
function possibleIndividualIds(sampleId: string | null | undefined): Set<string> | null {
  const sample = props.samples.find((candidate) => candidate.id === sampleId)
  if (!sample) return null
  const contact = props.contacts?.find((candidate) => candidate.id === sample.contact_id)
  const ids = contact
    ? [contact.donor_surface?.individual_id, contact.recipient_surface?.individual_id]
    : [sample.surface?.individual_id]
  return new Set(ids.filter((id): id is string => !!id))
}

function contributorOptionsFor(
  sampleId: string | null | undefined,
  selected: PCRContributorInput[],
) {
  const possible = possibleIndividualIds(sampleId)
  if (possible === null) return contributorOptions.value
  const keep = new Set([
    ...possible,
    ...selected.map((c) => c.individual_id).filter((id): id is string => !!id),
  ])
  return contributorOptions.value.filter(
    (option) => option.unknownLabel !== null || keep.has(option.id),
  )
}

function contributorKey(contributor: PCRContributorInput): string | null {
  if (contributor.individual_id) return contributor.individual_id
  if (contributor.unknown_label) {
    return (
      unknownPersonOptions.find((up) => up.unknownLabel === contributor.unknown_label)?.id ?? null
    )
  }
  return null
}

function emptyContributor(): PCRContributorInput {
  return { individual_id: null, unknown_label: null, mixture_proportion: null }
}

// Keeps the contributors array in sync with no_of_contributors: growing it
// adds blank rows, shrinking it drops the extra ones from the end.
function syncContributors(
  contributors: PCRContributorInput[],
  count: number | null,
): PCRContributorInput[] {
  const target = count ?? 0
  const next = contributors.slice(0, target)
  while (next.length < target) next.push(emptyContributor())
  return next
}

// The Samples tab passes its samples already in the user's sort order (see
// SamplesPanel), so results simply follow the position of their sample.
const sampleOrder = computed(
  () => new Map(props.samples.map((sample, index) => [sample.id, index])),
)

const allResults = ref<Result[]>([])
const loading = ref(false)
const loadError = ref('')

const results = computed(() =>
  allResults.value
    .filter((result) => result.sample_id != null && sampleOrder.value.has(result.sample_id))
    .sort((a, b) => sampleOrder.value.get(a.sample_id!)! - sampleOrder.value.get(b.sample_id!)!),
)

// The column sort is saved per user (all studies). With no sort, results
// keep the order of the Samples tab.
const { multiSortMeta, sorting, isCustom: isCustomSort, resetSort } = useTableSort('results')

// Plain text fields so the columns can sort and filter on them. Sorted here
// the same way the table sorts, so the CSV download matches the table.
const resultRows = computed(() =>
  sortRows(
    results.value.map((result) => ({
      ...result,
      scenarioNames: (props.surfaceScenarios[result.sample?.surface_id ?? ''] ?? []).join(', '),
      sampleLabel: sampleLabel(result.sample),
      sampleName: result.sample?.name ?? null,
      pcrCount: result.pcrs.length,
    })),
    multiSortMeta.value,
  ),
)

// -- Quick entry: one result per sample, then fill in the numbers --

const samplesWithoutResult = computed(() => {
  const withResult = new Set(allResults.value.map((result) => result.sample_id))
  return props.samples.filter((sample) => !withResult.has(sample.id))
})

const addingAll = ref(false)
const editMode = ref(false)

async function addResultsForAllSamples() {
  const missing = samplesWithoutResult.value
  if (!missing.length) return
  addingAll.value = true
  try {
    const created = await Promise.all(
      missing.map((sample) =>
        resultApi.create({
          sample_id: sample.id,
          quantification_method_id: null,
          dna_concentration: null,
          degradation_index: null,
          inhibition_category_id: null,
        }),
      ),
    )
    allResults.value = [...allResults.value, ...created]
    editMode.value = true
    toast.add({
      color: 'success',
      title: `Added ${created.length} result${created.length === 1 ? '' : 's'}`,
      description: 'Enter the DNA concentrations in the table, or use the CSV download and upload.',
    })
  } catch {
    loadError.value = 'Could not add the results. Please try again.'
  } finally {
    addingAll.value = false
  }
}

const numberOrNull = (value: number | null | undefined) =>
  value == null || Number.isNaN(value) ? null : value

function resultInputFrom(result: Result, dnaConcentration: number | null): ResultInput {
  return {
    sample_id: result.sample_id ?? null,
    quantification_method_id: result.quantification_method_id ?? null,
    dna_concentration: dnaConcentration,
    degradation_index: result.degradation_index ?? null,
    inhibition_category_id: result.inhibition_category_id ?? null,
  }
}

// Edit mode: each DNA concentration is saved as soon as it is committed.
async function saveConcentration(result: Result, value: number | null | undefined) {
  const next = numberOrNull(value)
  if (next === (result.dna_concentration ?? null)) return
  try {
    const updated = await resultApi.update(result.id, resultInputFrom(result, next))
    allResults.value = allResults.value.map((item) => (item.id === updated.id ? updated : item))
  } catch {
    loadError.value = 'Could not save this change. Please try again.'
  }
}

// -- CSV round trip --
// One row per genotyping result (or one empty row for a result without any).
// The two id columns identify rows and stay untouched; info_* columns give
// context; the numeric columns are editable. To add a genotyping result to a
// result, copy one of its rows, clear genotyping_id_do_not_edit and enter the
// values. New results inherit the methods of the result's latest genotyping run.

const CSV_ID = 'id_do_not_edit'
const CSV_PCR_ID = 'genotyping_id_do_not_edit'
const CSV_CONCENTRATION = 'dna_concentration_ng_ul'
const CSV_PCR_COLUMNS = {
  sample_input_volume_in_pcr: 'sample_input_volume_in_pcr_ul',
  dna_input_amount_in_pcr: 'dna_input_amount_in_pcr_pg',
  no_of_contributors: 'no_of_contributors',
  average_rfu: 'average_rfu',
  total_no_of_alleles: 'total_no_of_alleles',
} as const
type PcrNumericField = keyof typeof CSV_PCR_COLUMNS
const PCR_INTEGER_FIELDS: PcrNumericField[] = ['no_of_contributors', 'total_no_of_alleles']
const PCR_FIELDS = Object.keys(CSV_PCR_COLUMNS) as PcrNumericField[]

const CSV_EDITABLE_COLUMNS = [CSV_CONCENTRATION, ...Object.values(CSV_PCR_COLUMNS)]
const CSV_INFO_COLUMNS = [
  'info_scenario',
  'info_sample_name',
  'info_surface',
  'info_elution_volume_ul',
  'info_dna_quantity_ng',
  'info_pcr_method',
]
const CSV_NOTES = [
  'To add a genotyping result, copy a row of the same result, clear the cell in genotyping_id_do_not_edit and enter the values. Its methods are taken from the latest genotyping result of that result; set them in the table afterwards if needed.',
  'Genotyping results can not be deleted through the file; rows you remove are simply left unchanged.',
]

function scenarioNamesOf(result: Result): string {
  return (props.surfaceScenarios[result.sample?.surface_id ?? ''] ?? []).join('; ')
}

function buildCsvRows() {
  const header = [
    CSV_ID,
    CSV_PCR_ID,
    'info_scenario',
    'info_sample_name',
    'info_surface',
    'info_elution_volume_ul',
    CSV_CONCENTRATION,
    'info_dna_quantity_ng',
    'info_pcr_method',
    ...Object.values(CSV_PCR_COLUMNS),
  ]
  const rows = resultRows.value.flatMap((result) => {
    const base = [
      result.id,
      null as string | null,
      scenarioNamesOf(result),
      result.sample?.name,
      surfaceLabel(result.sample?.surface),
      result.sample?.elution_volume,
    ]
    const pcrs: (PCR | null)[] = result.pcrs.length ? result.pcrs : [null]
    return pcrs.map((pcr) => [
      base[0],
      pcr?.id ?? null,
      ...base.slice(2),
      result.dna_concentration,
      result.dna_quantity,
      pcr?.pcr_method ? methodLabel(pcr.pcr_method) : null,
      ...PCR_FIELDS.map((field) => pcr?.[field] ?? null),
    ])
  })
  return [header, ...rows]
}

interface CsvFailure {
  ok: false
  title: string
  description: string
}

async function applyCsvImport(table: string[][], decimal: DecimalSeparator) {
  const header = (table[0] ?? []).map((cell) => cell.trim().toLowerCase())
  const idCol = header.includes(CSV_ID) ? header.indexOf(CSV_ID) : header.indexOf('id')
  const pcrIdCol = header.indexOf(CSV_PCR_ID)
  const concentrationCol = header.indexOf(CSV_CONCENTRATION)
  const pcrCols = Object.fromEntries(
    PCR_FIELDS.map((field) => [field, header.indexOf(CSV_PCR_COLUMNS[field])]),
  ) as Record<PcrNumericField, number>
  const hasPcrCols = PCR_FIELDS.some((field) => pcrCols[field] !== -1)
  if (idCol === -1 || (concentrationCol === -1 && !hasPcrCols)) {
    return {
      ok: false,
      title: 'Unrecognized CSV',
      description: `Use a file downloaded from this table: it needs the column ${CSV_ID} and at least one of ${CSV_EDITABLE_COLUMNS.join(', ')}.`,
    } satisfies CsvFailure
  }

  const byId = new Map(results.value.map((result) => [result.id, result]))
  const problems: string[] = []

  // Per result: the new concentration and the full list of genotyping results to save.
  interface Plan {
    result: Result
    concentration: number | null | undefined
    pcrs: PCRInput[]
    pcrsChanged: boolean
    touchedPcrIds: Set<string>
  }
  const plans = new Map<string, Plan>()

  const parse = (cells: string[], col: number) =>
    col === -1 ? undefined : parseNumber(cells[col] ?? '', decimal)
  const invalid = (value: number | null | undefined, integer = false) =>
    value != null && (Number.isNaN(value) || value < 0 || (integer && !Number.isInteger(value)))

  table.slice(1).forEach((cells, index) => {
    const line = index + 2
    const result = byId.get((cells[idCol] ?? '').trim())
    if (!result) {
      problems.push(`line ${line}: unknown id`)
      return
    }
    let plan = plans.get(result.id)
    if (!plan) {
      plan = {
        result,
        concentration: undefined,
        pcrs: result.pcrs.map(pcrInputOf),
        pcrsChanged: false,
        touchedPcrIds: new Set(),
      }
      plans.set(result.id, plan)
    }

    // DNA concentration belongs to the result, so every row of it must agree.
    const concentration = parse(cells, concentrationCol)
    if (invalid(concentration)) {
      problems.push(
        `line ${line}: DNA concentration ${JSON.stringify(cells[concentrationCol])} is not a number of zero or more written with a "${decimal}" decimal separator`,
      )
      return
    }
    if (concentration !== undefined) {
      if (plan.concentration !== undefined && plan.concentration !== concentration) {
        problems.push(`line ${line}: DNA concentration differs between rows of the same result`)
        return
      }
      plan.concentration = concentration
    }

    const values = {} as Record<PcrNumericField, number | null | undefined>
    for (const field of PCR_FIELDS) {
      values[field] = parse(cells, pcrCols[field])
      if (invalid(values[field], PCR_INTEGER_FIELDS.includes(field))) {
        problems.push(
          `line ${line}: ${CSV_PCR_COLUMNS[field]} ${JSON.stringify(cells[pcrCols[field]])} must be ${PCR_INTEGER_FIELDS.includes(field) ? 'a whole number' : 'a number'} of zero or more${PCR_INTEGER_FIELDS.includes(field) ? '' : ` written with a "${decimal}" decimal separator`}`,
        )
        return
      }
    }

    const pcrId = pcrIdCol === -1 ? '' : (cells[pcrIdCol] ?? '').trim()
    const apply = (target: PCRInput) => {
      let changed = false
      for (const field of PCR_FIELDS) {
        const value = values[field]
        if (value !== undefined && value !== target[field]) {
          target[field] = value
          changed = true
        }
      }
      if (changed && values.no_of_contributors !== undefined) {
        target.contributors = syncContributors(target.contributors ?? [], target.no_of_contributors)
      }
      return changed
    }

    if (pcrId) {
      const position = result.pcrs.findIndex((pcr) => pcr.id === pcrId)
      if (position === -1) {
        problems.push(`line ${line}: unknown genotyping result id`)
        return
      }
      if (plan.touchedPcrIds.has(pcrId)) {
        problems.push(`line ${line}: genotyping result id appears more than once`)
        return
      }
      plan.touchedPcrIds.add(pcrId)
      if (apply(plan.pcrs[position]!)) plan.pcrsChanged = true
    } else if (PCR_FIELDS.some((field) => values[field] != null)) {
      // No genotyping id but values: a new genotyping result, with the methods
      // of the latest existing one.
      const latest = plan.pcrs.length ? plan.pcrs[plan.pcrs.length - 1] : null
      const fresh: PCRInput = latest
        ? {
            ...latest,
            contributors: [],
            ...Object.fromEntries(PCR_FIELDS.map((field) => [field, null])),
          }
        : emptyPcrForm()
      apply(fresh)
      plan.pcrs.push(fresh)
      plan.pcrsChanged = true
    }
  })

  if (problems.length) {
    return {
      ok: false,
      title: 'Nothing imported',
      description: `${problems.length} problem${problems.length === 1 ? '' : 's'}: ${problems.slice(0, 5).join('; ')}${problems.length > 5 ? ' …' : ''}`,
    } satisfies CsvFailure
  }

  const jobs = [...plans.values()].filter(
    (plan) =>
      plan.pcrsChanged ||
      (plan.concentration !== undefined &&
        plan.concentration !== (plan.result.dna_concentration ?? null)),
  )
  const updated = await Promise.all(
    jobs.map((plan) => {
      const input: ResultInput = {
        ...resultInputOf(plan.result),
        dna_concentration:
          plan.concentration === undefined
            ? (plan.result.dna_concentration ?? null)
            : plan.concentration,
      }
      if (plan.pcrsChanged) input.pcrs = plan.pcrs
      return resultApi.update(plan.result.id, input)
    }),
  )
  const updatedById = new Map(updated.map((result) => [result.id, result]))
  allResults.value = allResults.value.map((item) => updatedById.get(item.id) ?? item)
  return {
    ok: true,
    title: jobs.length
      ? `Updated ${jobs.length} result${jobs.length === 1 ? '' : 's'}`
      : 'No changes found',
  }
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    allResults.value = await resultApi.list({ study_id: props.studyId })
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
  ;[
    quantificationMethods.value,
    pcrMethods.value,
    postPcrTreatmentMethods.value,
    ceMethods.value,
    epgAnalysisMethods.value,
    epgInterpretationMethods.value,
  ] = await Promise.all([
    quantificationMethodApi.list(),
    pcrMethodApi.list(),
    postPcrTreatmentMethodApi.list(),
    ceMethodApi.list(),
    epgAnalysisMethodApi.list(),
    epgInterpretationMethodApi.list(),
  ])
})

function sampleLabel(sample?: Sample | null): string {
  return surfaceLabel(sample?.surface)
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

type ResultRow = (typeof resultRows.value)[number]

const view = useTableView(resultRows, {
  searchFields: ['sampleLabel', 'sampleName', 'scenarioNames', 'dna_concentration'],
  filters: { scenario: { field: 'scenarioNames' } },
  sorting,
  pageSize: 25,
})

const columns = computed<TableColumn<ResultRow>[]>(() => [
  expandColumn(),
  { id: 'sampleLabel', accessorKey: 'sampleLabel', header: sortHeader('Sample', { multi: true }) },
  { id: 'sampleName', accessorKey: 'sampleName', header: sortHeader('Name', { multi: true }) },
  {
    id: 'scenarioNames',
    accessorKey: 'scenarioNames',
    header: sortHeader('Scenario', { multi: true }),
  },
  {
    id: 'dna_concentration',
    accessorKey: 'dna_concentration',
    header: sortHeader('DNA concentration', { multi: true }),
  },
  {
    id: 'dna_quantity',
    accessorKey: 'dna_quantity',
    header: sortHeader('DNA quantity', { multi: true }),
  },
  {
    id: 'degradation_index',
    accessorKey: 'degradation_index',
    header: sortHeader('Degradation index', { multi: true }),
  },
  {
    id: 'pcrCount',
    header: sortHeader('Genotyping results', { multi: true }),
    meta: { class: { td: 'w-32' } },
  },
  ...(readOnly.value ? [] : [{ id: 'actions', header: '', meta: { class: { td: 'w-12' } } }]),
])

const pcrColumns = computed<TableColumn<PCR>[]>(() => [
  { id: 'pcr_method', header: 'PCR method' },
  { id: 'no_of_contributors', accessorKey: 'no_of_contributors', header: 'No. of contributors' },
  { id: 'average_rfu', accessorKey: 'average_rfu', header: 'Average RFU' },
  ...(readOnly.value ? [] : [{ id: 'actions', header: '', meta: { class: { td: 'w-12' } } }]),
])

// -- PCR form --
// pcrs is full-replace on Result update, so adding/editing/deleting one PCR
// run sends the whole list back with that one entry changed. The same form
// instance also backs the first PCR run embedded in the create-result
// dialog (see submitForm below), so the whole picture - sample, result
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
    average_rfu: null,
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
  average_rfu: yup.number().nullable().min(0, 'Average RFU must be zero or greater.'),
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
const [averageRfu] = definePcrField('average_rfu')
const [totalNoOfAlleles] = definePcrField('total_no_of_alleles')

// CE methods available for the currently-selected PCR method, falling back
// to the full list when none are linked yet (e.g. the lab hasn't set this
// up in Settings yet), so the dropdown is never left empty.
const ceMethodOptions = computed(() => {
  const matching = ceMethods.value.filter((method) => method.pcr_method_id === pcrMethodId.value)
  return matching.length ? matching : ceMethods.value
})
const ceMethodOptionLabels = computed(() => ceMethodLabels(ceMethodOptions.value))

watch(noOfContributors, (count) => {
  setPcrFieldValue('contributors', syncContributors(pcrFormValues.contributors ?? [], count))
})

// The form's values are read-only, so contributor rows are changed through
// setPcrFieldValue rather than by assigning to them in the template.
function updateContributor(index: number, patch: Partial<PCRContributorInput>) {
  const contributors = (pcrFormValues.contributors ?? []).map((contributor, i) =>
    i === index ? { ...contributor, ...patch } : { ...contributor },
  )
  setPcrFieldValue('contributors', contributors)
}

function setContributorKey(index: number, key: string | null) {
  const option = contributorOptions.value.find((candidate) => candidate.id === key)
  updateContributor(index, {
    individual_id: option && !option.unknownLabel ? option.id : null,
    unknown_label: option?.unknownLabel ?? null,
  })
}

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
    sample_id: null,
    quantification_method_id: null,
    dna_concentration: null,
    degradation_index: null,
    inhibition_category_id: null,
  }
}

const schema = yup.object({
  sample_id: yup.string().nullable().required('Please select a sample.'),
  quantification_method_id: yup.string().nullable().defined(),
  dna_concentration: yup.number().nullable().min(0, 'DNA concentration must be zero or greater.'),
  degradation_index: yup.number().nullable(),
  inhibition_category_id: yup.string().nullable().defined(),
})

const { defineField, errors, handleSubmit, resetForm } = useForm<ResultInput>({
  validationSchema: schema,
  initialValues: emptyForm(),
})

const [sampleId] = defineField('sample_id')
const [quantificationMethodId] = defineField('quantification_method_id')
const [dnaConcentration] = defineField('dna_concentration')
const [degradationIndex] = defineField('degradation_index')
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
  { value: 'pcr', title: 'First genotyping result', slot: 'pcr' },
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
      sample_id: row.sample_id ?? null,
      quantification_method_id: row.quantification_method_id ?? null,
      dna_concentration: row.dna_concentration ?? null,
      degradation_index: row.degradation_index ?? null,
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

function resultMenuItems(result: Result): ContextMenuItem[] {
  return [
    { label: 'Edit', icon: 'i-lucide-pencil', onSelect: () => openEditDialog(result) },
    {
      label: 'Delete',
      icon: 'i-lucide-trash-2',
      color: 'error',
      onSelect: () => deleteRow(result),
    },
  ]
}

// The right-clicked result's menu.
const resultContextMenuItems = ref<ContextMenuItem[]>([])

function onResultContextMenu(_event: Event, row: TableRow<ResultRow>) {
  resultContextMenuItems.value = readOnly.value ? [] : resultMenuItems(row.original)
}

// -- PCR dialog --
// Used for adding/editing/deleting PCR runs on an already-saved result
// (beyond the first one entered alongside the result itself).

const pcrDialogVisible = ref(false)
const pcrDialogResult = ref<Result | null>(null)
const editingPcrId = ref<string | null>(null)
const submittingPcr = ref(false)
const submitPcrError = ref('')

// DNA input amount (pg) = DNA concentration (ng/µL) × sample input volume
// (µL) × 1000. The backend recalculates it on save; here it is filled in
// live and locked whenever both values are known.
const pcrConcentration = computed(() =>
  pcrDialogVisible.value
    ? (pcrDialogResult.value?.dna_concentration ?? null)
    : (dnaConcentration.value ?? null),
)
const derivedDnaInputAmount = computed(() => {
  const concentration = pcrConcentration.value
  const volume = sampleInputVolumeInPcr.value
  return concentration == null || volume == null ? null : concentration * volume * 1000
})
const dnaInputAmountHelp = computed(() =>
  derivedDnaInputAmount.value !== null
    ? 'Calculated from DNA concentration × sample input volume.'
    : 'Calculated automatically once the DNA concentration and sample input volume are entered.',
)
watch(derivedDnaInputAmount, (amount) => {
  if (amount !== null) setPcrFieldValue('dna_input_amount_in_pcr', amount)
})

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
    average_rfu: pcr.average_rfu ?? null,
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
    submitPcrError.value = 'Could not save this genotyping result. Please try again.'
  } finally {
    submittingPcr.value = false
  }
})

function resultInputOf(result: Result): ResultInput {
  return {
    sample_id: result.sample_id ?? null,
    quantification_method_id: result.quantification_method_id ?? null,
    dna_concentration: result.dna_concentration ?? null,
    degradation_index: result.degradation_index ?? null,
    inhibition_category_id: result.inhibition_category_id ?? null,
  }
}

async function deletePcr(result: Result, pcr: PCR) {
  if (!window.confirm('Delete this genotyping result? This cannot be undone.')) return
  try {
    const nextPcrs = result.pcrs.filter((p) => p.id !== pcr.id).map(pcrInputOf)
    const updated = await resultApi.update(result.id, { ...resultInputOf(result), pcrs: nextPcrs })
    allResults.value = allResults.value.map((item) => (item.id === updated.id ? updated : item))
  } catch {
    loadError.value = 'Could not delete this genotyping result. Please try again.'
  }
}

// -- PCR row context menu --

function pcrMenuItems(result: Result, pcr: PCR): ContextMenuItem[] {
  return [
    { label: 'Edit', icon: 'i-lucide-pencil', onSelect: () => openEditPcrDialog(result, pcr) },
    {
      label: 'Delete',
      icon: 'i-lucide-trash-2',
      color: 'error',
      onSelect: () => deletePcr(result, pcr),
    },
  ]
}

// The right-clicked genotyping result's menu.
const pcrContextMenuItems = ref<ContextMenuItem[]>([])

function onPcrContextMenu(result: Result, row: TableRow<PCR>) {
  pcrContextMenuItems.value = readOnly.value ? [] : pcrMenuItems(result, row.original)
}
</script>

<template>
  <div class="flex flex-col gap-6" data-tour="results-panel">
    <div class="flex items-center justify-between">
      <p class="text-sm text-surface-500 dark:text-surface-400">
        Lab results derived from this scenario's samples.
      </p>
      <div v-if="!readOnly" class="flex flex-wrap gap-2" data-tour="results-actions">
        <UButton
          label="Add result for every sample"
          icon="i-lucide-list-plus"
          variant="outline"
          :loading="addingAll"
          :disabled="!samplesWithoutResult.length"
          @click="addResultsForAllSamples"
        />
        <UButton
          label="Add quantification result"
          icon="i-lucide-plus"
          variant="outline"
          :disabled="!samples.length"
          @click="openCreateDialog"
        />
      </div>
    </div>

    <UAlert
      v-if="!samples.length && !readOnly"
      color="info"
      variant="outline"
      description="Add a sample before recording results."
    />

    <UAlert v-if="loadError" color="error" variant="outline" :description="loadError" />

    <div class="flex flex-col gap-3">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex flex-wrap gap-2">
          <UButton
            type="button"
            icon="i-lucide-arrow-up-down"
            label="Reset sort"
            variant="outline"
            size="sm"
            :disabled="!isCustomSort"
            @click="resetSort()"
          />
          <UButton
            v-if="!readOnly"
            type="button"
            :label="editMode ? 'Done' : 'Edit values'"
            :icon="editMode ? 'i-lucide-check' : 'i-lucide-pencil'"
            :variant="editMode ? 'solid' : 'outline'"
            size="sm"
            :disabled="!results.length"
            @click="editMode = !editMode"
          />
          <CsvRoundTrip
            :disabled="!results.length"
            :filename="`${exportName ? `${exportName}_` : ''}results`"
            hint-key="results"
            :build-rows="buildCsvRows"
            :editable-columns="CSV_EDITABLE_COLUMNS"
            :info-columns="CSV_INFO_COLUMNS"
            :id-column="`${CSV_ID} and ${CSV_PCR_ID}`"
            :notes="CSV_NOTES"
            :apply-import="applyCsvImport"
          />
        </div>
        <div class="flex items-center gap-2">
          <UInput
            v-model="view.search"
            icon="i-lucide-search"
            placeholder="Keyword Search"
            class="w-full sm:w-64"
          />
          <TableFilterDrawer :active-count="view.activeFilterCount" @reset="view.resetFilters()">
            <UFormField label="Scenario">
              <UInput
                v-model="view.filters.scenario"
                placeholder="Search by scenario"
                class="w-full"
              />
            </UFormField>
          </TableFilterDrawer>
        </div>
      </div>
      <TableSortHint />

      <UContextMenu :items="resultContextMenuItems" :disabled="readOnly">
        <UTable
          v-model:expanded="expandedRows"
          v-model:sorting="view.sorting"
          :sorting-options="manualSorting"
          :data="view.rows"
          :columns="columns"
          :loading="loading"
          :get-row-id="(result: ResultRow) => result.id"
          empty="No results recorded yet."
          :on-contextmenu="onResultContextMenu"
        >
          <template #sampleName-cell="{ row }">{{ row.original.sampleName || '—' }}</template>
          <template #scenarioNames-cell="{ row }">
            <ScenarioBadges
              :names="surfaceScenarios[row.original.sample?.surface_id ?? ''] ?? []"
            />
          </template>
          <template #dna_concentration-cell="{ row: { original: data } }">
            <UFieldGroup v-if="editMode" class="w-full min-w-44">
              <UInputNumber
                :model-value="data.dna_concentration ?? undefined"
                :min="0"
                :step="0.1"
                :step-snapping="false"
                :format-options="{ maximumFractionDigits: 6 }"
                orientation="vertical"
                class="w-full"
                @update:model-value="(value: number | null) => saveConcentration(data, value)"
              />
              <UBadge color="neutral" variant="outline" size="lg" label="ng/µL" />
            </UFieldGroup>
            <template v-else>
              {{
                data.dna_concentration != null
                  ? `${auth.formatNumber(data.dna_concentration, FIXED4)} ng/µL`
                  : '—'
              }}
            </template>
          </template>
          <template #dna_quantity-cell="{ row: { original: data } }">
            {{
              data.dna_quantity != null ? `${auth.formatNumber(data.dna_quantity, FIXED4)} ng` : '—'
            }}
          </template>
          <template #degradation_index-cell="{ row: { original: data } }">
            {{ data.degradation_index != null ? auth.formatNumber(data.degradation_index) : '—' }}
          </template>
          <template #actions-cell="{ row }">
            <UDropdownMenu :items="resultMenuItems(row.original)" :content="{ align: 'end' }">
              <UButton
                icon="i-lucide-more-vertical"
                color="neutral"
                variant="ghost"
                square
                aria-label="Result options"
              />
            </UDropdownMenu>
          </template>

          <template #expanded="{ row: { original: result } }">
            <!-- Keep right-clicks in here from also opening the result's menu. -->
            <div class="flex flex-col gap-2 p-2" @contextmenu.stop>
              <div class="flex items-center justify-between">
                <h5 class="font-medium text-sm">Genotyping results</h5>
                <UButton
                  v-if="!readOnly"
                  label="Add genotyping result"
                  icon="i-lucide-plus"
                  variant="outline"
                  size="sm"
                  @click="openCreatePcrDialog(result)"
                />
              </div>
              <UContextMenu :items="pcrContextMenuItems" :disabled="readOnly">
                <UTable
                  :data="result.pcrs"
                  :columns="pcrColumns"
                  :get-row-id="(pcr: PCR) => pcr.id"
                  empty="No genotyping results recorded yet."
                  :on-contextmenu="(_e: Event, row: TableRow<PCR>) => onPcrContextMenu(result, row)"
                >
                  <template #pcr_method-cell="{ row }">
                    {{ row.original.pcr_method ? methodLabel(row.original.pcr_method) : '—' }}
                  </template>
                  <template #no_of_contributors-cell="{ row }">{{
                    row.original.no_of_contributors ?? '—'
                  }}</template>
                  <template #average_rfu-cell="{ row }">
                    {{
                      row.original.average_rfu != null
                        ? `${auth.formatNumber(row.original.average_rfu)} RFU`
                        : '—'
                    }}
                  </template>
                  <template #actions-cell="{ row }">
                    <UDropdownMenu
                      :items="pcrMenuItems(result, row.original)"
                      :content="{ align: 'end' }"
                    >
                      <UButton
                        icon="i-lucide-more-vertical"
                        color="neutral"
                        variant="ghost"
                        square
                        aria-label="Genotyping result options"
                      />
                    </UDropdownMenu>
                  </template>
                </UTable>
              </UContextMenu>
            </div>
          </template>
        </UTable>
      </UContextMenu>
      <TablePagination
        v-model:page="view.page"
        v-model:page-size="view.pageSize"
        :total="view.total"
        :page-sizes="[25, 50, 100, 200]"
      />
    </div>

    <UModal
      v-model:open="dialogVisible"
      :title="editingId === null ? 'Add quantification result' : 'Edit quantification result'"
      :ui="{ content: 'max-w-xl', footer: 'justify-end' }"
    >
      <template #body>
        <div v-if="editingId !== null" class="flex flex-col gap-4" data-tour="result-dialog">
          <SamplePicker v-model="sampleId" :samples="samples" :error="errors.sample_id" />

          <EntitySelect
            v-model="quantificationMethodId"
            label="Quantification method"
            :options="quantificationMethods"
            :option-label="methodLabel"
          />
          <p
            v-if="!quantificationMethods.length"
            class="text-sm text-surface-500 dark:text-surface-400 -mt-2"
          >
            No quantification methods yet. Add one under
            <RouterLink
              :to="{ name: 'settings-methods-quantification' }"
              class="underline"
              target="_blank"
            >
              Settings → Methods → Quantification </RouterLink
            >.
          </p>

          <UFormField label="DNA concentration" :error="errors.dna_concentration">
            <UFieldGroup>
              <UInputNumber
                v-model="dnaConcentration"
                :min="0"
                :step="0.1"
                :step-snapping="false"
                :format-options="{ maximumFractionDigits: 6 }"
                orientation="vertical"
                class="w-full"
              />
              <UBadge color="neutral" variant="outline" size="lg" label="ng/µL" />
            </UFieldGroup>
          </UFormField>
          <UFormField label="Degradation index" :error="errors.degradation_index">
            <UInputNumber
              v-model="degradationIndex"
              :step="0.01"
              :step-snapping="false"
              :format-options="{ maximumFractionDigits: 6 }"
              orientation="vertical"
              class="w-full"
            />
          </UFormField>

          <UAlert v-if="submitError" color="error" variant="outline" :description="submitError" />
        </div>

        <UStepper
          v-else
          v-model="activeStep"
          data-tour="result-dialog"
          :items="stepItems"
          :linear="false"
          class="bg-transparent!"
        >
          <template #result>
            <div class="flex flex-col gap-4">
              <SamplePicker v-model="sampleId" :samples="samples" :error="errors.sample_id" />

              <EntitySelect
                v-model="quantificationMethodId"
                label="Quantification method"
                :options="quantificationMethods"
                :option-label="methodLabel"
              />
              <p
                v-if="!quantificationMethods.length"
                class="text-sm text-surface-500 dark:text-surface-400 -mt-2"
              >
                No quantification methods yet. Add one under
                <RouterLink
                  :to="{ name: 'settings-methods-quantification' }"
                  class="underline"
                  target="_blank"
                >
                  Settings → Methods → Quantification </RouterLink
                >.
              </p>

              <UFormField label="DNA concentration" :error="errors.dna_concentration">
                <UFieldGroup>
                  <UInputNumber
                    v-model="dnaConcentration"
                    :step="0.0001"
                    :step-snapping="false"
                    :format-options="{ maximumFractionDigits: 6 }"
                    orientation="vertical"
                    class="w-full"
                  />
                  <UBadge color="neutral" variant="outline" size="lg" label="ng/µL" />
                </UFieldGroup>
              </UFormField>
              <UFormField label="Degradation index" :error="errors.degradation_index">
                <UInputNumber
                  v-model="degradationIndex"
                  :step="0.01"
                  :step-snapping="false"
                  :format-options="{ maximumFractionDigits: 6 }"
                  orientation="vertical"
                  class="w-full"
                />
              </UFormField>
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
                  <p
                    v-if="!pcrMethods.length"
                    class="text-sm text-surface-500 dark:text-surface-400"
                  >
                    No PCR methods yet. Add one under
                    <RouterLink
                      :to="{ name: 'settings-methods-pcr' }"
                      class="underline"
                      target="_blank"
                    >
                      Settings → Methods → PCR </RouterLink
                    >.
                  </p>
                </div>
                <div class="flex flex-col gap-1">
                  <EntitySelect
                    v-model="postPcrTreatmentMethodId"
                    label="Post-PCR treatment method"
                    :options="postPcrTreatmentMethods"
                    :option-label="(m: PostPCRTreatmentMethod) => `#${m.id}`"
                  />
                  <p
                    v-if="!postPcrTreatmentMethods.length"
                    class="text-sm text-surface-500 dark:text-surface-400"
                  >
                    No post-PCR treatment methods yet. Add one under
                    <RouterLink
                      :to="{ name: 'settings-methods-post-pcr-treatment' }"
                      class="underline"
                      target="_blank"
                    >
                      Settings → Methods → Post-PCR treatment </RouterLink
                    >.
                  </p>
                </div>
                <div class="flex flex-col gap-1">
                  <EntitySelect
                    v-model="ceMethodId"
                    label="CE method"
                    :options="ceMethodOptions"
                    :option-label="
                      (method) => ceMethodOptionLabels[method.id] ?? methodLabel(method)
                    "
                  />
                  <p
                    v-if="!ceMethods.length"
                    class="text-sm text-surface-500 dark:text-surface-400"
                  >
                    No CE methods yet. Add one under
                    <RouterLink
                      :to="{ name: 'settings-methods-ce' }"
                      class="underline"
                      target="_blank"
                    >
                      Settings → Methods → CE </RouterLink
                    >.
                  </p>
                </div>
                <div class="flex flex-col gap-1">
                  <EntitySelect
                    v-model="epgAnalysisMethodId"
                    label="EPG analysis method"
                    :options="epgAnalysisMethods"
                    :option-label="methodLabel"
                  />
                  <p
                    v-if="!epgAnalysisMethods.length"
                    class="text-sm text-surface-500 dark:text-surface-400"
                  >
                    No EPG analysis methods yet. Add one under
                    <RouterLink
                      :to="{ name: 'settings-methods-epg-analysis' }"
                      class="underline"
                      target="_blank"
                    >
                      Settings → Methods → EPG analysis </RouterLink
                    >.
                  </p>
                </div>
                <div class="flex flex-col gap-1">
                  <EntitySelect
                    v-model="epgInterpretationMethodId"
                    label="EPG interpretation method"
                    :options="epgInterpretationMethods"
                    :option-label="methodLabel"
                  />
                  <p
                    v-if="!epgInterpretationMethods.length"
                    class="text-sm text-surface-500 dark:text-surface-400"
                  >
                    No EPG interpretation methods yet. Add one under
                    <RouterLink
                      :to="{ name: 'settings-methods-epg-interpretation' }"
                      class="underline"
                      target="_blank"
                    >
                      Settings → Methods → EPG interpretation </RouterLink
                    >.
                  </p>
                </div>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <UFormField
                  label="Sample input volume in PCR"
                  :error="pcrErrors.sample_input_volume_in_pcr"
                >
                  <UFieldGroup>
                    <UInputNumber
                      v-model="sampleInputVolumeInPcr"
                      :step="0.1"
                      :step-snapping="false"
                      :format-options="{ maximumFractionDigits: 6 }"
                      orientation="vertical"
                      class="w-full"
                    />
                    <UBadge color="neutral" variant="outline" size="lg" label="µL" />
                  </UFieldGroup>
                </UFormField>
                <UFormField
                  label="DNA input amount in PCR"
                  :error="pcrErrors.dna_input_amount_in_pcr"
                  :help="dnaInputAmountHelp"
                >
                  <UFieldGroup>
                    <UInputNumber
                      v-model="dnaInputAmountInPcr"
                      :disabled="derivedDnaInputAmount !== null"
                      :step="0.001"
                      :step-snapping="false"
                      :format-options="{ maximumFractionDigits: 6 }"
                      orientation="vertical"
                      class="w-full"
                    />
                    <UBadge color="neutral" variant="outline" size="lg" label="pg" />
                  </UFieldGroup>
                </UFormField>
                <UFormField label="No. of contributors" :error="pcrErrors.no_of_contributors">
                  <UInputNumber
                    v-model="noOfContributors"
                    :min="0"
                    orientation="vertical"
                    class="w-full"
                  />
                </UFormField>
                <UFormField label="Average RFU" :error="pcrErrors.average_rfu">
                  <UFieldGroup>
                    <UInputNumber
                      v-model="averageRfu"
                      :min="0"
                      :step="0.1"
                      :step-snapping="false"
                      :format-options="{ maximumFractionDigits: 6 }"
                      orientation="vertical"
                      class="w-full"
                    />
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
                      :items="contributorOptionsFor(sampleId, pcrFormValues.contributors ?? [])"
                      value-key="id"
                      placeholder="Select an individual or unknown person"
                      clear
                      class="w-full"
                      @update:model-value="setContributorKey(index, $event)"
                    />
                  </UFormField>
                  <UFormField label="Mx" class="w-28">
                    <UInputNumber
                      :model-value="contributor.mixture_proportion"
                      @update:model-value="
                        updateContributor(index, { mixture_proportion: $event ?? null })
                      "
                      :min="0"
                      :max="1"
                      :step="0.01"
                      :step-snapping="false"
                      :format-options="{ maximumFractionDigits: 6 }"
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

              <UAlert
                v-if="submitError"
                color="error"
                variant="outline"
                :description="submitError"
              />
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
                <RouterLink
                  :to="{ name: 'settings-methods-pcr' }"
                  class="underline"
                  target="_blank"
                >
                  Settings → Methods → PCR </RouterLink
                >.
              </p>
            </div>
            <div class="flex flex-col gap-1">
              <EntitySelect
                v-model="postPcrTreatmentMethodId"
                label="Post-PCR treatment method"
                :options="postPcrTreatmentMethods"
                :option-label="(m: PostPCRTreatmentMethod) => `#${m.id}`"
              />
              <p
                v-if="!postPcrTreatmentMethods.length"
                class="text-sm text-surface-500 dark:text-surface-400"
              >
                No post-PCR treatment methods yet. Add one under
                <RouterLink
                  :to="{ name: 'settings-methods-post-pcr-treatment' }"
                  class="underline"
                  target="_blank"
                >
                  Settings → Methods → Post-PCR treatment </RouterLink
                >.
              </p>
            </div>
            <div class="flex flex-col gap-1">
              <EntitySelect
                v-model="ceMethodId"
                label="CE method"
                :options="ceMethodOptions"
                :option-label="(method) => ceMethodOptionLabels[method.id] ?? methodLabel(method)"
              />
              <p v-if="!ceMethods.length" class="text-sm text-surface-500 dark:text-surface-400">
                No CE methods yet. Add one under
                <RouterLink :to="{ name: 'settings-methods-ce' }" class="underline" target="_blank">
                  Settings → Methods → CE </RouterLink
                >.
              </p>
            </div>
            <div class="flex flex-col gap-1">
              <EntitySelect
                v-model="epgAnalysisMethodId"
                label="EPG analysis method"
                :options="epgAnalysisMethods"
                :option-label="methodLabel"
              />
              <p
                v-if="!epgAnalysisMethods.length"
                class="text-sm text-surface-500 dark:text-surface-400"
              >
                No EPG analysis methods yet. Add one under
                <RouterLink
                  :to="{ name: 'settings-methods-epg-analysis' }"
                  class="underline"
                  target="_blank"
                >
                  Settings → Methods → EPG analysis </RouterLink
                >.
              </p>
            </div>
            <div class="flex flex-col gap-1">
              <EntitySelect
                v-model="epgInterpretationMethodId"
                label="EPG interpretation method"
                :options="epgInterpretationMethods"
                :option-label="methodLabel"
              />
              <p
                v-if="!epgInterpretationMethods.length"
                class="text-sm text-surface-500 dark:text-surface-400"
              >
                No EPG interpretation methods yet. Add one under
                <RouterLink
                  :to="{ name: 'settings-methods-epg-interpretation' }"
                  class="underline"
                  target="_blank"
                >
                  Settings → Methods → EPG interpretation </RouterLink
                >.
              </p>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <UFormField
              label="Sample input volume in PCR"
              :error="pcrErrors.sample_input_volume_in_pcr"
            >
              <UFieldGroup>
                <UInputNumber
                  v-model="sampleInputVolumeInPcr"
                  :step="0.1"
                  :step-snapping="false"
                  :format-options="{ maximumFractionDigits: 6 }"
                  orientation="vertical"
                  class="w-full"
                />
                <UBadge color="neutral" variant="outline" size="lg" label="µL" />
              </UFieldGroup>
            </UFormField>
            <UFormField
              label="DNA input amount in PCR"
              :error="pcrErrors.dna_input_amount_in_pcr"
              :help="dnaInputAmountHelp"
            >
              <UFieldGroup>
                <UInputNumber
                  v-model="dnaInputAmountInPcr"
                  :disabled="derivedDnaInputAmount !== null"
                  :step="0.001"
                  :step-snapping="false"
                  :format-options="{ maximumFractionDigits: 6 }"
                  orientation="vertical"
                  class="w-full"
                />
                <UBadge color="neutral" variant="outline" size="lg" label="pg" />
              </UFieldGroup>
            </UFormField>
            <UFormField label="No. of contributors" :error="pcrErrors.no_of_contributors">
              <UInputNumber
                v-model="noOfContributors"
                :min="0"
                orientation="vertical"
                class="w-full"
              />
            </UFormField>
            <UFormField label="Average RFU" :error="pcrErrors.average_rfu">
              <UFieldGroup>
                <UInputNumber
                  v-model="averageRfu"
                  :min="0"
                  :step="0.1"
                  :step-snapping="false"
                  :format-options="{ maximumFractionDigits: 6 }"
                  orientation="vertical"
                  class="w-full"
                />
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
                  :items="
                    contributorOptionsFor(
                      pcrDialogResult?.sample_id,
                      pcrFormValues.contributors ?? [],
                    )
                  "
                  value-key="id"
                  placeholder="Select an individual or unknown person"
                  clear
                  class="w-full"
                  @update:model-value="setContributorKey(index, $event)"
                />
              </UFormField>
              <UFormField label="Mx" class="w-28">
                <UInputNumber
                  :model-value="contributor.mixture_proportion"
                  @update:model-value="
                    updateContributor(index, { mixture_proportion: $event ?? null })
                  "
                  :min="0"
                  :max="1"
                  :step="0.01"
                  :step-snapping="false"
                  :format-options="{ maximumFractionDigits: 6 }"
                  orientation="vertical"
                  class="w-full"
                />
              </UFormField>
            </div>
          </div>

          <UAlert
            v-if="submitPcrError"
            color="error"
            variant="outline"
            :description="submitPcrError"
          />
        </div>
      </template>
      <template #footer>
        <UButton
          label="Cancel"
          icon="i-lucide-x"
          variant="ghost"
          @click="pcrDialogVisible = false"
        />
        <UButton
          label="Save"
          icon="i-lucide-save"
          :loading="submittingPcr"
          @click="submitPcrForm"
        />
      </template>
    </UModal>
  </div>
</template>
