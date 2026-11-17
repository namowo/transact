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
import SamplePicker from '@/components/scenarios/SamplePicker.vue'
import { surfaceLabel } from '@/components/data/sampleLabel'
import ScenarioBadges from '@/components/data/ScenarioBadges.vue'
import { useAuthStore } from '@/stores/auth'
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
import { degradationCategoryApi } from '@/api/categories'
import type {
  Contact,
  Sample,
  Result,
  ResultInput,
  PCR,
  PCRInput,
  PCRContributor,
  PCRContributorInput,
  QuantificationMethod,
  PCRMethod,
  PostPCRTreatmentMethod,
  CEMethod,
  EPGAnalysisMethod,
  EPGInterpretationMethod,
} from '@/api/types'

const props = defineProps<{
  samples: Sample[]
  studyId: string
  surfaceScenarios: Record<string, string[]>
  contacts?: Contact[]
  exportName?: string
}>()

const auth = useAuthStore()
const FIXED4 = { minimumFractionDigits: 4, maximumFractionDigits: 4 }
const toast = useToast()

const { individuals, individualOptions, individualName } = useIndividualOptions(props.studyId)

// Contributor picker options: known Individuals plus as many "UPn" (unknown
// person) placeholders as could ever be needed. Unknown persons aren't
// their own entity - just an auto-numbered label scoped to one PCR run.
const MAX_CONTRIBUTORS = 8
// Mixture proportions are decimal fractions (0-1) with up to 5 decimals.
const MX_FORMAT = { maximumFractionDigits: 5 }
const unknownPersonOptions = Array.from({ length: MAX_CONTRIBUTORS }, (_, i) => ({
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

// Each individual / unknown person can only be picked once per run, so
// options chosen on other rows are left out.
function contributorOptionsFor(
  sampleId: string | null | undefined,
  selected: PCRContributorInput[],
  currentIndex: number,
) {
  const takenElsewhere = new Set(
    selected
      .filter((_, index) => index !== currentIndex)
      .map((c) => contributorKey(c))
      .filter((key): key is string => !!key),
  )
  const options = contributorOptions.value.filter((option) => !takenElsewhere.has(option.id))
  const possible = possibleIndividualIds(sampleId)
  if (possible === null) return options
  const keep = new Set([...possible, ...selected.map((c) => c.individual_id).filter((id): id is string => !!id)])
  return options.filter((option) => option.unknownLabel !== null || keep.has(option.id))
}

function contributorKey(contributor: PCRContributorInput): string | null {
  if (contributor.individual_id) return contributor.individual_id
  if (contributor.unknown_label) {
    return unknownPersonOptions.find((up) => up.unknownLabel === contributor.unknown_label)?.id ?? null
  }
  return null
}

function emptyContributor(): PCRContributorInput {
  return { individual_id: null, unknown_label: null, mixture_proportion: null }
}

// Mixture proportions may never exceed 1 in total, and once every contributor
// has one they must add up to exactly 1. The tolerance absorbs rounding to
// 5 decimals (e.g. 3 × 0.33333).
const MX_SUM_TOLERANCE = 1e-4
function mixtureSumProblem(contributors: PCRContributorInput[] | null | undefined): string | null {
  const values = (contributors ?? []).map((contributor) => contributor.mixture_proportion)
  const filled = values.filter((value): value is number => value != null)
  if (!filled.length) return null
  const sum = filled.reduce((total, value) => total + value, 0)
  const complete = filled.length === values.length
  if (sum <= 1 + MX_SUM_TOLERANCE && (!complete || sum >= 1 - MX_SUM_TOLERANCE)) return null
  return `Mixture proportions must add up to 1 (currently ${Number(sum.toFixed(5))}).`
}

// Keeps the contributors array in sync with no_of_contributors: growing it
// adds blank rows, shrinking it drops the extra ones from the end.
function syncContributors(contributors: PCRContributorInput[], count: number | null): PCRContributorInput[] {
  const target = Math.min(Math.max(count ?? 0, 0), MAX_CONTRIBUTORS)
  const next = contributors.slice(0, target)
  while (next.length < target) next.push(emptyContributor())
  return next
}

// The Samples tab passes its samples already in the user's sort order (see
// SamplesPanel), so results simply follow the position of their sample.
const sampleOrder = computed(() => new Map(props.samples.map((sample, index) => [sample.id, index])))

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
const { multiSortMeta, isCustom: isCustomSort, resetSort } = useTableSort('results')

// Plain text fields so the columns can sort and filter on them. Sorted here
// the same way the table sorts, so the CSV download matches the table.
const resultRows = computed(() =>
  sortRows(
    results.value.map((result) => ({
      ...result,
      scenarioNames: (props.surfaceScenarios[result.sample?.surface_id ?? ''] ?? []).join(', '),
      sampleLabel: sampleLabel(result.sample),
      sampleName: result.sample?.name ?? null,
      degradationLabel: result.degradation_category?.name ?? null,
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

// The quick-entry dialog asks how many genotyping runs each sample gets, so
// the empty runs are created up front and only need their values filled in.
// The optional methods are applied to every created result and run.
const MAX_RUNS_PER_SAMPLE = 20
const quickAddVisible = ref(false)
const quickAdd = ref({
  runsPerSample: 1 as number | null,
  quantification_method_id: null as string | null,
  pcr_method_id: null as string | null,
  post_pcr_treatment_method_id: null as string | null,
  ce_method_id: null as string | null,
  epg_analysis_method_id: null as string | null,
  epg_interpretation_method_id: null as string | null,
})

const quickAddCeMethodOptions = computed(() => {
  const matching = ceMethods.value.filter((method) => method.pcr_method_id === quickAdd.value.pcr_method_id)
  return matching.length ? matching : ceMethods.value
})

function openQuickAddDialog() {
  loadError.value = ''
  quickAddVisible.value = true
}

async function addResultsForAllSamples() {
  const missing = samplesWithoutResult.value
  if (!missing.length) return
  const settings = quickAdd.value
  const runs = Math.min(Math.max(Math.trunc(settings.runsPerSample ?? 0), 0), MAX_RUNS_PER_SAMPLE)
  const run = (): PCRInput => ({
    ...emptyPcrForm(),
    pcr_method_id: settings.pcr_method_id,
    post_pcr_treatment_method_id: settings.post_pcr_treatment_method_id,
    ce_method_id: settings.ce_method_id,
    epg_analysis_method_id: settings.epg_analysis_method_id,
    epg_interpretation_method_id: settings.epg_interpretation_method_id,
  })
  addingAll.value = true
  try {
    const created = await Promise.all(
      missing.map((sample) =>
        resultApi.create({
          sample_id: sample.id,
          quantification_method_id: settings.quantification_method_id,
          dna_concentration: null,
          degradation_category_id: null,
          inhibition_category_id: null,
          pcrs: Array.from({ length: runs }, run),
        }),
      ),
    )
    allResults.value = [...allResults.value, ...created]
    if (runs) {
      expandedRows.value = {
        ...expandedRows.value,
        ...Object.fromEntries(created.map((result) => [result.id, true])),
      }
    }
    editMode.value = true
    quickAddVisible.value = false
    const runText = runs ? ` with ${runs} genotyping run${runs === 1 ? '' : 's'} each` : ''
    toast.add({
      color: 'success',
      title: `Added ${created.length} result${created.length === 1 ? '' : 's'}${runText}`,
      description: 'Enter the values in the table, or use the CSV download and upload.',
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
    degradation_category_id: result.degradation_category_id ?? null,
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

// Edit mode: genotyping run values are saved as soon as they are committed.
// Runs are full-replace on update (the backend recreates them, so their ids
// change), hence saves for one result run one after another, each built from
// the latest saved state, so quick consecutive edits never overwrite each other.
const pcrSaveQueues = new Map<string, Promise<void>>()

function savePcrField(resultId: string, index: number, field: PcrNumericField, value: number | null | undefined) {
  const next = numberOrNull(value)
  const previous = pcrSaveQueues.get(resultId) ?? Promise.resolve()
  const job = previous.then(async () => {
    const result = allResults.value.find((item) => item.id === resultId)
    const pcr = result?.pcrs[index]
    if (!result || !pcr || next === (pcr[field] ?? null)) return
    const pcrs = result.pcrs.map(pcrInputOf)
    const target = pcrs[index]!
    target[field] = next
    if (field === 'no_of_contributors') {
      target.contributors = syncContributors(target.contributors ?? [], next)
      const problem = mixtureSumProblem(target.contributors)
      if (problem) {
        loadError.value = `${problem} Adjust them in the genotyping result dialog.`
        return
      }
    }
    try {
      const updated = await resultApi.update(result.id, { ...resultInputOf(result), pcrs })
      allResults.value = allResults.value.map((item) => (item.id === updated.id ? updated : item))
    } catch {
      loadError.value = 'Could not save this change. Please try again.'
    }
  })
  pcrSaveQueues.set(resultId, job)
}

const PCR_EDIT_COLUMNS: { field: PcrNumericField; header: string; unit?: string; integer?: boolean; step?: number; max?: number }[] = [
  { field: 'sample_input_volume_in_pcr', header: 'Sample input volume', unit: 'µL', step: 0.1 },
  { field: 'dna_input_amount_in_pcr', header: 'DNA input amount', unit: 'pg', step: 0.001 },
  { field: 'no_of_contributors', header: 'No. of contributors', integer: true, max: MAX_CONTRIBUTORS },
  { field: 'total_rfu', header: 'Total RFU', unit: 'RFU', step: 0.1 },
  { field: 'total_no_of_alleles', header: 'Total no. of alleles', integer: true },
]

function formatPcrValue(value: number | null | undefined, unit?: string): string {
  if (value == null) return '—'
  return unit ? `${auth.formatNumber(value)} ${unit}` : String(value)
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
  total_rfu: 'total_rfu',
  total_no_of_alleles: 'total_no_of_alleles',
} as const
type PcrNumericField = keyof typeof CSV_PCR_COLUMNS
const PCR_INTEGER_FIELDS: PcrNumericField[] = ['no_of_contributors', 'total_no_of_alleles']
const PCR_FIELDS = Object.keys(CSV_PCR_COLUMNS) as PcrNumericField[]

// Contributors as pairs of columns: who (an individual's name or UP1-UP8)
// and their mixture proportion.
const CSV_CONTRIBUTOR_COLUMNS = Array.from({ length: MAX_CONTRIBUTORS }, (_, i) => ({
  who: `contributor_${i + 1}`,
  mx: `mx_${i + 1}`,
}))
const CSV_EDITABLE_COLUMNS = [
  CSV_CONCENTRATION,
  ...Object.values(CSV_PCR_COLUMNS),
  ...CSV_CONTRIBUTOR_COLUMNS.flatMap(({ who, mx }) => [who, mx]),
]
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
  `Contributors go in contributor_1 to contributor_${MAX_CONTRIBUTORS}: the individual's name as shown in the app, or UP1 to UP${MAX_CONTRIBUTORS} for unknown persons. Each is followed by its mixture proportion (mx_1 …) as a decimal between 0 and 1 with up to 5 decimals; together they must add up to 1. Only the first no_of_contributors pairs may be filled.`,
]

function csvContributorName(contributor: PCRContributor): string | null {
  if (contributor.unknown_label) return contributor.unknown_label
  if (!contributor.individual_id) return null
  const individual = individuals.value.find((candidate) => candidate.id === contributor.individual_id)
  return individual ? individualName(individual) : (contributor.individual?.name ?? null)
}

// Resolves a contributor cell to an individual or unknown person, or returns
// an error message.
function resolveCsvContributor(text: string): Pick<PCRContributorInput, 'individual_id' | 'unknown_label'> | string {
  const up = /^up\s*(\d+)$/i.exec(text)
  if (up) {
    const number = Number(up[1])
    if (number >= 1 && number <= MAX_CONTRIBUTORS) return { individual_id: null, unknown_label: `UP${number}` }
    return `${JSON.stringify(text)} is not a valid unknown person (UP1 to UP${MAX_CONTRIBUTORS})`
  }
  const wanted = text.toLowerCase()
  const matches = individuals.value.filter((individual) => individualName(individual).trim().toLowerCase() === wanted)
  if (matches.length === 1) return { individual_id: matches[0]!.id, unknown_label: null }
  if (matches.length > 1) return `${JSON.stringify(text)} matches more than one individual`
  return `${JSON.stringify(text)} is not an individual of this study`
}

function sameContributors(a: PCRContributorInput[], b: PCRContributorInput[]): boolean {
  return (
    a.length === b.length &&
    a.every(
      (contributor, i) =>
        (contributor.individual_id ?? null) === (b[i]!.individual_id ?? null) &&
        (contributor.unknown_label ?? null) === (b[i]!.unknown_label ?? null) &&
        (contributor.mixture_proportion ?? null) === (b[i]!.mixture_proportion ?? null),
    )
  )
}

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
    ...CSV_CONTRIBUTOR_COLUMNS.flatMap(({ who, mx }) => [who, mx]),
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
      ...CSV_CONTRIBUTOR_COLUMNS.flatMap((_, i) => {
        const contributor = pcr?.contributors?.[i]
        return contributor ? [csvContributorName(contributor), contributor.mixture_proportion ?? null] : [null, null]
      }),
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
  const pcrCols = Object.fromEntries(PCR_FIELDS.map((field) => [field, header.indexOf(CSV_PCR_COLUMNS[field])])) as Record<
    PcrNumericField,
    number
  >
  const contributorCols = CSV_CONTRIBUTOR_COLUMNS.map(({ who, mx }) => ({ who: header.indexOf(who), mx: header.indexOf(mx) }))
  const hasContributorCols = contributorCols.some(({ who, mx }) => who !== -1 || mx !== -1)
  const hasPcrCols = hasContributorCols || PCR_FIELDS.some((field) => pcrCols[field] !== -1)
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

  const parse = (cells: string[], col: number) => (col === -1 ? undefined : parseNumber(cells[col] ?? '', decimal))
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
      problems.push(`line ${line}: DNA concentration ${JSON.stringify(cells[concentrationCol])} is not a number of zero or more written with a "${decimal}" decimal separator`)
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
    if (values.no_of_contributors != null && values.no_of_contributors > MAX_CONTRIBUTORS) {
      problems.push(`line ${line}: ${CSV_PCR_COLUMNS.no_of_contributors} must be at most ${MAX_CONTRIBUTORS}`)
      return
    }

    // Contributor pairs; undefined when the file has no contributor columns,
    // which leaves the existing contributors as they are.
    let csvContributors: PCRContributorInput[] | undefined
    if (hasContributorCols) {
      csvContributors = []
      const possible = possibleIndividualIds(result.sample_id)
      const current = new Set(
        result.pcrs.flatMap((pcr) => pcr.contributors ?? []).map((c) => c.individual_id).filter(Boolean),
      )
      const seen = new Set<string>()
      for (const [i, cols] of contributorCols.entries()) {
        const { who: whoColumn, mx: mxColumn } = CSV_CONTRIBUTOR_COLUMNS[i]!
        const contributor = emptyContributor()
        const who = cols.who === -1 ? '' : (cells[cols.who] ?? '').trim()
        if (who) {
          const resolved = resolveCsvContributor(who)
          if (typeof resolved === 'string') {
            problems.push(`line ${line}: ${whoColumn} ${resolved}`)
            return
          }
          const { individual_id: individualId } = resolved
          if (individualId && possible && !possible.has(individualId) && !current.has(individualId)) {
            problems.push(`line ${line}: ${whoColumn} ${JSON.stringify(who)} is not a donor or recipient of this sample's contact`)
            return
          }
          const key = individualId ?? resolved.unknown_label!
          if (seen.has(key)) {
            problems.push(`line ${line}: ${whoColumn} ${JSON.stringify(who)} is listed more than once`)
            return
          }
          seen.add(key)
          Object.assign(contributor, resolved)
        }
        const mx = parse(cells, cols.mx)
        if (mx != null) {
          if (Number.isNaN(mx) || mx < 0 || mx > 1 || Math.abs(mx * 1e5 - Math.round(mx * 1e5)) > 1e-6) {
            problems.push(
              `line ${line}: ${mxColumn} ${JSON.stringify(cells[cols.mx])} must be a number between 0 and 1 with at most 5 decimals, written with a "${decimal}" decimal separator`,
            )
            return
          }
          contributor.mixture_proportion = mx
        }
        csvContributors.push(contributor)
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
      const count = target.no_of_contributors ?? 0
      let contributors = syncContributors(target.contributors ?? [], target.no_of_contributors)
      if (csvContributors) {
        const overflow = csvContributors.findIndex((c, i) => i >= count && !isBlankContributor(c))
        if (overflow !== -1) {
          problems.push(
            `line ${line}: ${CSV_CONTRIBUTOR_COLUMNS[overflow]!.who} is filled, but no_of_contributors is ${count}`,
          )
          return changed
        }
        contributors = csvContributors.slice(0, count)
      }
      if (!sameContributors(contributors, target.contributors ?? [])) {
        target.contributors = contributors
        changed = true
        const problem = mixtureSumProblem(contributors)
        if (problem) problems.push(`line ${line}: ${problem}`)
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
    } else if (
      PCR_FIELDS.some((field) => values[field] != null) ||
      csvContributors?.some((contributor) => !isBlankContributor(contributor))
    ) {
      // No genotyping id but values: a new genotyping result, with the methods
      // of the latest existing one.
      const latest = plan.pcrs.length ? plan.pcrs[plan.pcrs.length - 1] : null
      const fresh: PCRInput = latest
        ? { ...latest, contributors: [], ...Object.fromEntries(PCR_FIELDS.map((field) => [field, null])) }
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
      (plan.concentration !== undefined && plan.concentration !== (plan.result.dna_concentration ?? null)),
  )
  const updated = await Promise.all(
    jobs.map((plan) => {
      const input: ResultInput = {
        ...resultInputOf(plan.result),
        dna_concentration:
          plan.concentration === undefined ? (plan.result.dna_concentration ?? null) : plan.concentration,
      }
      if (plan.pcrsChanged) input.pcrs = plan.pcrs
      return resultApi.update(plan.result.id, input)
    }),
  )
  const updatedById = new Map(updated.map((result) => [result.id, result]))
  allResults.value = allResults.value.map((item) => updatedById.get(item.id) ?? item)
  return {
    ok: true,
    title: jobs.length ? `Updated ${jobs.length} result${jobs.length === 1 ? '' : 's'}` : 'No changes found',
  }
}

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

function initFilters() {
  return {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
    scenarioNames: { value: null, matchMode: FilterMatchMode.CONTAINS },
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
    .min(0, 'No. of contributors must be zero or greater.')
    .max(MAX_CONTRIBUTORS, `No. of contributors can be at most ${MAX_CONTRIBUTORS}.`),
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
          .max(1, 'Mixture proportion must be between 0 and 1.')
          .test(
            'max-5-decimals',
            'Mixture proportion can have at most 5 decimal places.',
            (value) => value == null || Math.abs(value * 1e5 - Math.round(value * 1e5)) < 1e-6,
          ),
      }),
    )
    .defined()
    .test('mx-sum', function (contributors) {
      const problem = mixtureSumProblem(contributors as PCRContributorInput[])
      return problem ? this.createError({ message: problem }) : true
    }),
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

// useForm's values are read-only, so contributor rows are changed through
// setFieldValue rather than by assigning to them.
function updateContributor(index: number, changes: Partial<PCRContributorInput>) {
  const contributors = (pcrFormValues.contributors ?? []).map((contributor, i) =>
    i === index ? { ...contributor, ...changes } : { ...contributor },
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

function setMixtureProportion(index: number, value: number | null | undefined) {
  updateContributor(index, { mixture_proportion: value ?? null })
}

// Shown live while typing; the schema test still blocks saving.
const mixtureSumError = computed(() => mixtureSumProblem(pcrFormValues.contributors) ?? pcrErrors.value.contributors)

function mixtureProportionError(index: number): string | undefined {
  return (pcrErrors.value as Record<string, string | undefined>)[`contributors[${index}].mixture_proportion`]
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
    degradation_category_id: null,
    inhibition_category_id: null,
  }
}

const schema = yup.object({
  sample_id: yup.string().nullable().required('Please select a sample.'),
  quantification_method_id: yup.string().nullable().defined(),
  dna_concentration: yup.number().nullable().min(0, 'DNA concentration must be zero or greater.'),
  degradation_category_id: yup.string().nullable().defined(),
  inhibition_category_id: yup.string().nullable().defined(),
})

const { defineField, errors, handleSubmit, resetForm } = useForm<ResultInput>({
  validationSchema: schema,
  initialValues: emptyForm(),
})

const [sampleId] = defineField('sample_id')
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
    degradation_category_id: result.degradation_category_id ?? null,
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
        Lab results derived from this scenario's samples.
      </p>
      <div class="flex flex-wrap gap-2">
        <UButton
          label="Add result for every sample"
          icon="i-lucide-list-plus"
          variant="outline"
          :loading="addingAll"
          :disabled="!samplesWithoutResult.length"
          @click="openQuickAddDialog"
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
      v-if="!samples.length"
      color="info"
      variant="outline"
      description="Add a sample before recording results."
    />

    <UAlert v-if="loadError" color="error" variant="outline" :description="loadError" />

    <ContextMenu ref="resultContextMenu" :model="resultContextMenuItems" />

    <div class="flex flex-col gap-3">
      <div class="flex items-center justify-between gap-3">
        <div class="flex flex-wrap gap-2">
          <UButton type="button" icon="i-lucide-filter-x" variant="outline" size="sm" @click="clearFilters()">
            Clear Filters
          </UButton>
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
        <UInput
          v-model="(filters['global'] as { value: string | null }).value"
          type="text"
          icon="i-lucide-search"
          placeholder="Keyword Search"
        />
      </div>
      <TableSortHint />

      <div class="overflow-x-auto">
        <DataTable
          v-model:filters="filters"
          v-model:expanded-rows="expandedRows"
          v-model:multi-sort-meta="multiSortMeta"
          :value="resultRows"
          :loading="loading"
          data-key="id"
          sort-mode="multiple"
          paginator
          :rows="25"
          :rowsPerPageOptions="[25, 50, 100, 200]"
          filterDisplay="menu"
          removableSort
          :globalFilterFields="['sample.surface.id', 'dna_concentration', 'scenarioNames']"
          @row-contextmenu="({ originalEvent, data }: { originalEvent: Event; data: Result }) => openResultContextMenu(originalEvent, data)"
        >
          <template #empty>No results recorded yet.</template>
          <Column expander style="width: 2.5rem" />
          <Column field="sampleLabel" header="Sample" sortable>
            <template #body="{ data }">{{ data.sampleLabel }}</template>
          </Column>
          <Column field="sampleName" header="Name" sortable>
            <template #body="{ data }">{{ data.sampleName || '—' }}</template>
          </Column>
          <Column
            field="scenarioNames"
            header="Scenario"
            sortable
            :showFilterOperator="false"
            :showAddButton="false"
          >
            <template #body="{ data }"><ScenarioBadges :names="surfaceScenarios[data.sample?.surface_id] ?? []" /></template>
            <template #filter="{ filterModel }">
              <UInput v-model="filterModel.value" type="text" placeholder="Search by scenario" />
            </template>
          </Column>
          <Column
            field="dna_concentration"
            header="DNA concentration"
            sortable
          >
            <template #body="{ data }">
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
                {{ data.dna_concentration != null ? `${auth.formatNumber(data.dna_concentration, FIXED4)} ng/µL` : '—' }}
              </template>
            </template>
          </Column>
          <Column field="dna_quantity" header="DNA quantity" sortable>
            <template #body="{ data }">
              {{ data.dna_quantity != null ? `${auth.formatNumber(data.dna_quantity, FIXED4)} ng` : '—' }}
            </template>
          </Column>
          <Column field="degradationLabel" header="Degradation Index" sortable>
            <template #body="{ data }">{{ data.degradationLabel ?? '—' }}</template>
          </Column>
          <Column field="pcrCount" header="Genotyping results" sortable style="width: 8rem">
            <template #body="{ data }">{{ data.pcrCount }}</template>
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
              <!-- No data-key: rows are keyed by position, because saving a run
                   recreates all runs with new ids and inputs must keep focus. -->
              <DataTable
                :value="result.pcrs"
                @row-contextmenu="({ originalEvent, data }: { originalEvent: Event; data: PCR }) => openPcrContextMenu(originalEvent, result, data)"
              >
                <template #empty>No genotyping results recorded yet.</template>
                <Column header="Run" style="width: 3.5rem">
                  <template #body="{ index }">{{ index + 1 }}</template>
                </Column>
                <Column header="PCR method">
                  <template #body="{ data }">{{ data.pcr_method ? methodLabel(data.pcr_method) : '—' }}</template>
                </Column>
                <Column v-for="col in PCR_EDIT_COLUMNS" :key="col.field" :header="col.header">
                  <template #body="{ data, index }">
                    <UFieldGroup v-if="editMode" class="w-full min-w-36">
                      <UInputNumber
                        :model-value="data[col.field] ?? undefined"
                        :min="0"
                        :max="col.max"
                        :step="col.integer ? 1 : col.step"
                        :step-snapping="!!col.integer"
                        :format-options="col.integer ? { maximumFractionDigits: 0 } : { maximumFractionDigits: 6 }"
                        orientation="vertical"
                        class="w-full"
                        @update:model-value="(value: number | null) => savePcrField(result.id, index, col.field, value)"
                      />
                      <UBadge v-if="col.unit" color="neutral" variant="outline" size="lg" :label="col.unit" />
                    </UFieldGroup>
                    <template v-else>{{ formatPcrValue(data[col.field], col.unit) }}</template>
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
    </div>

    <UModal
      v-model:open="dialogVisible"
      :title="editingId === null ? 'Add quantification result' : 'Edit quantification result'"
      :ui="{ content: 'max-w-3xl', footer: 'justify-end' }"
    >
      <template #body>
        <div v-if="editingId !== null" class="flex flex-col gap-4">
          <SamplePicker v-model="sampleId" :samples="samples" :error="errors.sample_id" />

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
              <UInputNumber v-model="dnaConcentration" :min="0" :step="0.1" :step-snapping="false" :format-options="{ maximumFractionDigits: 6 }" orientation="vertical" class="w-full" />
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
              <SamplePicker v-model="sampleId" :samples="samples" :error="errors.sample_id" />

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
                  <UInputNumber v-model="dnaConcentration" :step="0.0001" :step-snapping="false" :format-options="{ maximumFractionDigits: 6 }" orientation="vertical" class="w-full" />
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
                    <UInputNumber v-model="sampleInputVolumeInPcr" :step="0.1" :step-snapping="false" :format-options="{ maximumFractionDigits: 6 }" orientation="vertical" class="w-full" />
                    <UBadge color="neutral" variant="outline" size="lg" label="µL" />
                  </UFieldGroup>
                </UFormField>
                <UFormField label="DNA input amount in PCR" :error="pcrErrors.dna_input_amount_in_pcr">
                  <UFieldGroup>
                    <UInputNumber v-model="dnaInputAmountInPcr" :step="0.001" :step-snapping="false" :format-options="{ maximumFractionDigits: 6 }" orientation="vertical" class="w-full" />
                    <UBadge color="neutral" variant="outline" size="lg" label="pg" />
                  </UFieldGroup>
                </UFormField>
                <UFormField label="Total RFU" :error="pcrErrors.total_rfu">
                  <UFieldGroup>
                    <UInputNumber v-model="totalRfu" :min="0" :step="0.1" :step-snapping="false" :format-options="{ maximumFractionDigits: 6 }" orientation="vertical" class="w-full" />
                    <UBadge color="neutral" variant="outline" size="lg" label="RFU" />
                  </UFieldGroup>
                </UFormField>
                <UFormField label="Total no. of alleles" :error="pcrErrors.total_no_of_alleles">
                  <UInputNumber v-model="totalNoOfAlleles" orientation="vertical" class="w-full" />
                </UFormField>
              </div>

              <UCard variant="subtle" :ui="{ body: 'p-4 sm:p-4' }">
                <template #header>
                  <UFormField
                    label="No. of contributors"
                    :description="`Up to ${MAX_CONTRIBUTORS} people, each with their mixture proportion (Mx, 0–1).`"
                    :error="pcrErrors.no_of_contributors"
                    orientation="horizontal"
                  >
                    <UInputNumber v-model="noOfContributors" :min="0" :max="MAX_CONTRIBUTORS" orientation="vertical" class="w-28" />
                  </UFormField>
                </template>
                <template v-if="pcrFormValues.contributors?.length" #default>
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-3">
                    <div
                      v-for="(contributor, index) in pcrFormValues.contributors"
                      :key="index"
                      class="flex items-start gap-2"
                    >
                      <UFormField :label="`Contributor ${index + 1}`" class="flex-1 min-w-0">
                        <USelectMenu
                          :model-value="contributorKey(contributor)"
                          :items="contributorOptionsFor(sampleId, pcrFormValues.contributors ?? [], index)"
                          value-key="id"
                          placeholder="Individual or unknown"
                          clear
                          class="w-full"
                          @update:model-value="setContributorKey(index, $event)"
                        />
                      </UFormField>
                      <UFormField label="Mx" :error="mixtureProportionError(index)" class="w-32 shrink-0">
                        <UInputNumber
                          :model-value="contributor.mixture_proportion ?? undefined"
@update:model-value="(value: number | null) => setMixtureProportion(index, value)"
                          :min="0"
                          :max="1"
                          :step="0.01"
                          :step-snapping="false"
                          :format-options="MX_FORMAT"
                          placeholder="0–1"
                          orientation="vertical"
                          class="w-full"
                        />
                      </UFormField>
                  </div>
                  </div>
                  <p v-if="mixtureSumError" class="mt-3 text-sm text-error">{{ mixtureSumError }}</p>
                </template>
              </UCard>

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
      v-model:open="quickAddVisible"
      title="Add result for every sample"
      :description="`Creates a result for the ${samplesWithoutResult.length} sample${samplesWithoutResult.length === 1 ? '' : 's'} without one.`"
      :ui="{ content: 'max-w-xl', footer: 'justify-end' }"
    >
      <template #body>
        <div class="flex flex-col gap-4">
          <UFormField
            label="Genotyping runs per sample"
            help="Each result gets this many empty genotyping results, ready to fill in."
          >
            <UInputNumber
              v-model="quickAdd.runsPerSample"
              :min="0"
              :max="MAX_RUNS_PER_SAMPLE"
              orientation="vertical"
              class="w-40"
            />
          </UFormField>

          <USeparator label="Methods (optional, used for every entry)" />

          <EntitySelect
            v-model="quickAdd.quantification_method_id"
            label="Quantification method"
            :options="quantificationMethods"
            :option-label="methodLabel"
          />
          <div v-if="quickAdd.runsPerSample" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <EntitySelect
              v-model="quickAdd.pcr_method_id"
              label="PCR method"
              :options="pcrMethods"
              :option-label="methodLabel"
            />
            <EntitySelect
              v-model="quickAdd.post_pcr_treatment_method_id"
              label="Post-PCR treatment method"
              :options="postPcrTreatmentMethods"
              :option-label="(m: PostPCRTreatmentMethod) => `#${m.id}`"
            />
            <EntitySelect
              v-model="quickAdd.ce_method_id"
              label="CE method"
              :options="quickAddCeMethodOptions"
              :option-label="methodLabel"
            />
            <EntitySelect
              v-model="quickAdd.epg_analysis_method_id"
              label="EPG analysis method"
              :options="epgAnalysisMethods"
              :option-label="methodLabel"
            />
            <EntitySelect
              v-model="quickAdd.epg_interpretation_method_id"
              label="EPG interpretation method"
              :options="epgInterpretationMethods"
              :option-label="methodLabel"
            />
          </div>

          <UAlert v-if="loadError" color="error" variant="outline" :description="loadError" />
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="quickAddVisible = false" />
        <UButton
          :label="`Add ${samplesWithoutResult.length} result${samplesWithoutResult.length === 1 ? '' : 's'}`"
          icon="i-lucide-list-plus"
          :loading="addingAll"
          @click="addResultsForAllSamples"
        />
      </template>
    </UModal>

    <UModal
      v-model:open="pcrDialogVisible"
      :title="editingPcrId === null ? 'Add genotyping result' : 'Edit genotyping result'"
      :ui="{ content: 'max-w-3xl', footer: 'justify-end' }"
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
                <UInputNumber v-model="sampleInputVolumeInPcr" :step="0.1" :step-snapping="false" :format-options="{ maximumFractionDigits: 6 }" orientation="vertical" class="w-full" />
                <UBadge color="neutral" variant="outline" size="lg" label="µL" />
              </UFieldGroup>
            </UFormField>
            <UFormField label="DNA input amount in PCR" :error="pcrErrors.dna_input_amount_in_pcr">
              <UFieldGroup>
                <UInputNumber v-model="dnaInputAmountInPcr" :step="0.001" :step-snapping="false" :format-options="{ maximumFractionDigits: 6 }" orientation="vertical" class="w-full" />
                <UBadge color="neutral" variant="outline" size="lg" label="pg" />
              </UFieldGroup>
            </UFormField>
            <UFormField label="Total RFU" :error="pcrErrors.total_rfu">
              <UFieldGroup>
                <UInputNumber v-model="totalRfu" :min="0" :step="0.1" :step-snapping="false" :format-options="{ maximumFractionDigits: 6 }" orientation="vertical" class="w-full" />
                <UBadge color="neutral" variant="outline" size="lg" label="RFU" />
              </UFieldGroup>
            </UFormField>
            <UFormField label="Total no. of alleles" :error="pcrErrors.total_no_of_alleles">
              <UInputNumber v-model="totalNoOfAlleles" orientation="vertical" class="w-full" />
            </UFormField>
          </div>

          <UCard variant="subtle" :ui="{ body: 'p-4 sm:p-4' }">
            <template #header>
              <UFormField
                label="No. of contributors"
                :description="`Up to ${MAX_CONTRIBUTORS} people, each with their mixture proportion (Mx, 0–1).`"
                :error="pcrErrors.no_of_contributors"
                orientation="horizontal"
              >
                <UInputNumber v-model="noOfContributors" :min="0" :max="MAX_CONTRIBUTORS" orientation="vertical" class="w-28" />
              </UFormField>
            </template>
            <template v-if="pcrFormValues.contributors?.length" #default>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-3">
                <div
                  v-for="(contributor, index) in pcrFormValues.contributors"
                  :key="index"
                  class="flex items-start gap-2"
                >
                  <UFormField :label="`Contributor ${index + 1}`" class="flex-1 min-w-0">
                    <USelectMenu
                      :model-value="contributorKey(contributor)"
                      :items="contributorOptionsFor(pcrDialogResult?.sample_id, pcrFormValues.contributors ?? [], index)"
                      value-key="id"
                      placeholder="Individual or unknown"
                      clear
                      class="w-full"
                      @update:model-value="setContributorKey(index, $event)"
                    />
                  </UFormField>
                  <UFormField label="Mx" :error="mixtureProportionError(index)" class="w-32 shrink-0">
                    <UInputNumber
                      :model-value="contributor.mixture_proportion ?? undefined"
@update:model-value="(value: number | null) => setMixtureProportion(index, value)"
                      :min="0"
                      :max="1"
                      :step="0.01"
                      :step-snapping="false"
                      :format-options="MX_FORMAT"
                      placeholder="0–1"
                      orientation="vertical"
                      class="w-full"
                    />
                  </UFormField>
              </div>
              </div>
              <p v-if="mixtureSumError" class="mt-3 text-sm text-error">{{ mixtureSumError }}</p>
            </template>
          </UCard>

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
