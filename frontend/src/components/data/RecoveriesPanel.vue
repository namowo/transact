<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import { FilterMatchMode } from '@openvue/core/api'
import DataTableSkeleton from '@/components/data/DataTableSkeleton.vue'
import EntitySelect from '@/components/scenarios/EntitySelect.vue'
import InlineCreatableSelect from '@/components/scenarios/InlineCreatableSelect.vue'
import ScenarioBadges from '@/components/data/ScenarioBadges.vue'
import SurfaceMultiSelect from './SurfaceMultiSelect.vue'
import { downloadTextFile, parseCsv, parseNumber, toCsv, type DecimalSeparator } from './csv'
import { useToast } from '@nuxt/ui/composables'
import { templateName } from './contactTemplateLabel'
import { surfaceLabel, recoverySetLabel, extractionMethodLabel, samplingMethodLabel } from './recoveryLabel'
import { recoveryApi, recoverySetApi, samplingMethodApi, extractionMethodApi } from '@/api/methods'
import { useAuthStore } from '@/stores/auth'
import type {
  Contact,
  ContactTemplate,
  Recovery,
  RecoveryInput,
  RecoverySet,
  Scenario,
  SamplingMethod,
  ExtractionMethod,
  Surface,
} from '@/api/types'

const props = defineProps<{
  studyId: string
  contacts: Contact[]
  contactTemplates: ContactTemplate[]
  surfaceScenarios: Record<string, string[]>
  scenarios: Scenario[]
  exportName?: string
}>()

const emit = defineEmits<{
  'update:recoveries': [recoveries: Recovery[]]
}>()

const auth = useAuthStore()

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
    items: items.map((recovery) => ({
      ...recovery,
      scenarioNames: (props.surfaceScenarios[recovery.surface_id ?? ''] ?? []).join(', '),
    })),
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
    scenarioNames: { value: null, matchMode: FilterMatchMode.CONTAINS },
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
    name: null,
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
  name: yup.string().nullable().defined(),
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

const [name] = defineField('name')
const [surfaceId] = defineField('surface_id')
const [recoverySetId] = defineField('recovery_set_id')
const [samplingMethodId] = defineField('sampling_method_id')
const [extractionMethodId] = defineField('extraction_method_id')
const [elutionVolume] = defineField('elution_volume')
const [area] = defineField('area')

// Create mode: the selected contact sides ("<contact id>|<side>"), one recovery each.
const surfaceIds = ref<string[]>([])

function contactLabelFor(contactId: string | null | undefined): string {
  const index = props.contacts.findIndex((contact) => contact.id === contactId)
  if (index === -1) return '—'
  const contact = props.contacts[index]!
  const template = props.contactTemplates.find((t) => t.id === contact.contact_template_id)
  const base = contact.name || `Contact ${index + 1}`
  return template ? `${base} (${templateName(template)})` : base
}

function surfaceEntryLabel(surfaceId: string): string {
  return surfaceLabel(studySurfaces.value.find((s) => s.id === surfaceId))
}

// Name template for batch-created recoveries: {#} -> 1, 2, 3; {##} -> 01, 02;
// {###} -> 001, 002 ... (the number of #s is the minimum digit count).
const nameTemplate = ref('')
const templateInput = ref<{ inputRef?: HTMLInputElement | null } | null>(null)

// Inserts a placeholder at the cursor (or replaces the selection) in the name template.
function insertTemplateToken(token: string) {
  const input = templateInput.value?.inputRef
  const current = nameTemplate.value
  const start = input?.selectionStart ?? current.length
  const end = input?.selectionEnd ?? current.length
  nameTemplate.value = current.slice(0, start) + token + current.slice(end)
  const caret = start + token.length
  void nextTick(() => {
    input?.focus()
    input?.setSelectionRange(caret, caret)
  })
}

function applyNameTemplate(template: string, index: number): string {
  return template.replace(/\{(#+)\}/g, (_, hashes: string) => String(index).padStart(hashes.length, '0'))
}

// Recovery names must be unique within the study (case-insensitive).
const normalizeName = (value: string | null | undefined) => (value ?? '').trim().toLowerCase()

const studyRecoveryNames = computed(() =>
  allRecoveries.value.filter((recovery) => recovery.study_id === props.studyId),
)

function nameTaken(name: string | null | undefined, ignoreId: string | null = null): boolean {
  const wanted = normalizeName(name)
  if (!wanted) return false
  return studyRecoveryNames.value.some(
    (recovery) => recovery.id !== ignoreId && normalizeName(recovery.name) === wanted,
  )
}

// Continues the numbering of earlier batches: with "Sample 01" to "Sample 20"
// already recorded, the template "Sample {##}" starts at 21. The first
// placeholder in the template is the counter; the pattern is matched against
// existing names.
const templateStart = computed(() => {
  const template = nameTemplate.value.trim()
  if (!template || !/\{#+\}/.test(template)) return 1
  const escape = (text: string) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  let seenCounter = false
  const pattern = template
    .split(/(\{#+\})/)
    .map((part) => {
      if (!/^\{#+\}$/.test(part)) return escape(part)
      if (seenCounter) return '\\d+'
      seenCounter = true
      return '(\\d+)'
    })
    .join('')
  const regex = new RegExp(`^${pattern}$`, 'i')
  let highest = 0
  for (const recovery of studyRecoveryNames.value) {
    const match = regex.exec((recovery.name ?? '').trim())
    if (match) highest = Math.max(highest, parseInt(match[1]!, 10))
  }
  return highest + 1
})

function generatedName(index: number): string | null {
  const template = nameTemplate.value.trim()
  return template ? applyNameTemplate(template, templateStart.value + index) : null
}

const dialogVisible = ref(false)
// Create mode runs in two steps inside one dialog: 1 = pick surfaces and
// shared settings, 2 = per-recovery details. Nothing is saved until step 2.
const step = ref<1 | 2>(1)
const editingId = ref<string | null>(null)
const submitting = ref(false)
const submitError = ref('')

async function openCreateDialog() {
  editingId.value = null
  resetForm({ values: emptyForm() })
  surfaceIds.value = []
  nameTemplate.value = ''
  detailRows.value = []
  step.value = 1
  submitError.value = ''
  dialogVisible.value = true
  recoverySetId.value = await ensureDefaultRecoverySet()
}

function openEditDialog(row: Recovery) {
  editingId.value = row.id
  resetForm({
    values: {
      name: row.name ?? null,
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
  surfaceIds.value = []
  step.value = 1
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
      goToDetailsStep(formValues)
      return
    } else {
      if (nameTaken(formValues.name, editingId.value)) {
        submitError.value = 'This name is already used by another recovery. Names must be unique.'
        return
      }
      const updated = await recoveryApi.update(editingId.value, {
        ...formValues,
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

// -- Step 2: per-recovery details, then create the whole batch --

interface DetailRow {
  key: string
  contactId: string
  surfaceId: string
  name: string | null
  elutionVolume: number | null
  area: number | null
}

const detailRows = ref<DetailRow[]>([])
const sharedValues = ref<RecoveryInput | null>(null)
const bulkOpen = ref(false)
const bulkElutionVolume = ref<number | null>(null)
const bulkArea = ref<number | null>(null)

// Names that clash with an existing recovery or appear twice in this batch.
const duplicateRowNames = computed(() => {
  const counts = new Map<string, number>()
  for (const row of detailRows.value) {
    const key = normalizeName(row.name)
    if (key) counts.set(key, (counts.get(key) ?? 0) + 1)
  }
  return new Set(
    detailRows.value
      .filter((row) => nameTaken(row.name) || (counts.get(normalizeName(row.name)) ?? 0) > 1)
      .map((row) => row.key),
  )
})

// Fills a value into every row; a field left empty is not touched.
function applyToAllRows() {
  for (const row of detailRows.value) {
    if (bulkElutionVolume.value != null && !Number.isNaN(bulkElutionVolume.value))
      row.elutionVolume = bulkElutionVolume.value
    if (bulkArea.value != null && !Number.isNaN(bulkArea.value)) row.area = bulkArea.value
  }
  bulkOpen.value = false
}

// Builds one row per selected surface. Rows for surfaces that stay selected
// keep what was already entered, so going back and forth loses nothing; names
// still following the template are regenerated if the order changed.
function goToDetailsStep(formValues: RecoveryInput) {
  sharedValues.value = formValues
  const existing = new Map(detailRows.value.map((row) => [row.key, row]))
  const rows: DetailRow[] = []
  surfaceIds.value.forEach((key) => {
    const [contactId, side] = key.split('|') as [string, 'donor_surface' | 'recipient_surface']
    const surface = props.contacts.find((contact) => contact.id === contactId)?.[side]
    if (!surface) return
    rows.push(
      existing.get(key) ?? {
        key,
        contactId,
        surfaceId: surface.id,
        name: generatedName(rows.length),
        elutionVolume: null,
        area: null,
      },
    )
  })
  detailRows.value = rows
  bulkElutionVolume.value = null
  bulkArea.value = null
  bulkOpen.value = false
  step.value = 2
}

async function createRecoveries() {
  if (!sharedValues.value) return
  submitting.value = true
  submitError.value = ''
  try {
    const created = await Promise.all(
      detailRows.value.map(({ contactId, surfaceId, name, elutionVolume, area }) =>
        recoveryApi.create({
          ...sharedValues.value!,
          contact_id: contactId,
          surface_id: surfaceId,
          name: name?.trim() || null,
          elution_volume: numberOrNull(elutionVolume),
          area: numberOrNull(area),
        }),
      ),
    )
    allRecoveries.value = [...allRecoveries.value, ...created]
    dialogVisible.value = false
  } catch {
    submitError.value = 'Could not create these recoveries. Please try again.'
  } finally {
    submitting.value = false
  }
}

// -- CSV round trip --
// Download the study's recoveries, edit the numeric values in a spreadsheet,
// and upload the file again. Rows are matched by their id column; only the
// elution volume and area are read back.

const toast = useToast()
const importing = ref(false)

// Columns: the id identifies the row and must stay untouched; the info_*
// columns only give context; name, volume and area are the editable ones.
const CSV_ID = 'id_do_not_edit'
const CSV_NAME = 'name'
const CSV_VOLUME = 'elution_volume_ul'
const CSV_AREA = 'area_cm2'
const CSV_HEADER = [
  CSV_ID,
  'info_scenario',
  'info_contact',
  'info_surface',
  'info_recovery_set',
  CSV_NAME,
  CSV_VOLUME,
  CSV_AREA,
]

// A short explanation is shown before each download until the user opts out.
const CSV_HINT_KEY = 'transact.recoveries.csvHintDismissed'
const csvHintVisible = ref(false)
const csvHintDontShowAgain = ref(false)

function csvHintDismissed(): boolean {
  try {
    return localStorage.getItem(CSV_HINT_KEY) === '1'
  } catch {
    return false
  }
}

function onDownloadClick() {
  if (csvHintDismissed()) {
    downloadCsv()
    return
  }
  csvHintDontShowAgain.value = false
  csvHintVisible.value = true
}

function confirmCsvDownload() {
  if (csvHintDontShowAgain.value) {
    try {
      localStorage.setItem(CSV_HINT_KEY, '1')
    } catch {
      // Storage unavailable: the hint simply shows again next time.
    }
  }
  csvHintVisible.value = false
  downloadCsv()
}

// Scenarios of the contact the sample belongs to (via its template); recoveries
// without a contact fall back to the scenarios of their surface.
function recoveryScenarioNames(recovery: Recovery): string[] {
  const contact = props.contacts.find((c) => c.id === recovery.contact_id)
  if (contact) {
    return props.scenarios
      .filter((s) => s.contact_templates.some((t) => t.id === contact.contact_template_id))
      .map((s) => s.name)
  }
  return props.surfaceScenarios[recovery.surface_id ?? ''] ?? []
}

function downloadCsv() {
  const rows = recoveries.value.map((recovery) => [
    recovery.id,
    recoveryScenarioNames(recovery).join('; '),
    contactLabelFor(recovery.contact_id),
    surfaceLabel(recovery.surface),
    recoverySetLabel(recoverySets.value.find((set) => set.id === recovery.recovery_set_id) ?? null),
    recovery.name,
    recovery.elution_volume,
    recovery.area,
  ])
  const date = new Date().toISOString().slice(0, 10)
  const prefix = props.exportName ? `${props.exportName}_` : ''
  // CSV files always use a point as decimal separator, whatever the profile's number format.
  downloadTextFile(`${prefix}recoveries_${date}.csv`, toCsv([CSV_HEADER, ...rows]))
  // The next step of the round trip: edit the file, then upload it here.
  openImportDialog()
}

const importDialogVisible = ref(false)
const pendingCsvFile = ref<File | null>(null)
const decimalSeparator = ref<DecimalSeparator>(auth.decimalSeparator)

const decimalOptions = [
  { value: '.', label: 'Point', description: 'Example: 1.5' },
  { value: ',', label: 'Comma', description: 'Example: 1,5' },
]
function openImportDialog() {
  pendingCsvFile.value = null
  decimalSeparator.value = auth.decimalSeparator
  importDialogVisible.value = true
}

async function importCsv() {
  const file = pendingCsvFile.value
  if (!file) return
  const decimal = decimalSeparator.value
  importDialogVisible.value = false
  importing.value = true
  try {
    const table = parseCsv(await file.text())
    const header = (table[0] ?? []).map((cell) => cell.trim().toLowerCase())
    // "id" is accepted for files exported before the column was renamed.
    const idCol = header.includes(CSV_ID) ? header.indexOf(CSV_ID) : header.indexOf('id')
    const nameCol = header.indexOf(CSV_NAME)
    const volumeCol = header.indexOf(CSV_VOLUME)
    const areaCol = header.indexOf(CSV_AREA)
    if (idCol === -1 || (nameCol === -1 && volumeCol === -1 && areaCol === -1)) {
      toast.add({
        color: 'error',
        title: 'Unrecognized CSV',
        description: `Use a file downloaded from this table: it needs the columns ${CSV_ID} and at least one of ${CSV_NAME}, ${CSV_VOLUME}, ${CSV_AREA}.`,
      })
      return
    }

    const byId = new Map(recoveries.value.map((recovery) => [recovery.id, recovery]))
    const changes: {
      recovery: Recovery
      name: string | null
      elution_volume: number | null
      area: number | null
    }[] = []
    const problems: string[] = []
    const seenIds = new Set<string>()
    table.slice(1).forEach((cells, index) => {
      const line = index + 2
      const id = (cells[idCol] ?? '').trim()
      const recovery = byId.get(id)
      if (!recovery) {
        problems.push(`line ${line}: unknown id`)
        return
      }
      if (seenIds.has(id)) {
        problems.push(`line ${line}: id appears more than once`)
        return
      }
      seenIds.add(id)
      const name = nameCol === -1 ? (recovery.name ?? null) : (cells[nameCol] ?? '').trim() || null
      const volume = volumeCol === -1 ? (recovery.elution_volume ?? null) : parseNumber(cells[volumeCol] ?? '', decimal)
      const area = areaCol === -1 ? (recovery.area ?? null) : parseNumber(cells[areaCol] ?? '', decimal)
      if ((volume !== null && (Number.isNaN(volume) || volume < 0)) || (area !== null && (Number.isNaN(area) || area < 0))) {
        const bad = [
          volumeCol !== -1 && !(volume === null || (!Number.isNaN(volume) && volume >= 0)) ? `${CSV_VOLUME} ${JSON.stringify(cells[volumeCol])}` : '',
          areaCol !== -1 && !(area === null || (!Number.isNaN(area) && area >= 0)) ? `${CSV_AREA} ${JSON.stringify(cells[areaCol])}` : '',
        ].filter(Boolean).join(', ')
        problems.push(`line ${line}: ${bad} is not a number of zero or more written with a "${decimal}" decimal separator (choose the other one in the upload dialog if the file uses it)`)
        return
      }
      if (
        name !== (recovery.name ?? null) ||
        volume !== (recovery.elution_volume ?? null) ||
        area !== (recovery.area ?? null)
      ) {
        changes.push({ recovery, name, elution_volume: volume, area })
      }
    })

    // Names must stay unique across the whole study once the changes are applied.
    if (!problems.length) {
      const finalNames = new Map(studyRecoveryNames.value.map((recovery) => [recovery.id, recovery.name ?? null]))
      for (const change of changes) finalNames.set(change.recovery.id, change.name)
      const owners = new Map<string, number>()
      for (const name of finalNames.values()) {
        const key = normalizeName(name)
        if (key) owners.set(key, (owners.get(key) ?? 0) + 1)
      }
      for (const change of changes) {
        if ((owners.get(normalizeName(change.name)) ?? 0) > 1) {
          problems.push(`name "${change.name}" would not be unique`)
        }
      }
    }

    if (problems.length) {
      toast.add({
        color: 'error',
        title: 'Nothing imported',
        description: `${problems.length} problem${problems.length === 1 ? '' : 's'}: ${problems.slice(0, 5).join('; ')}${problems.length > 5 ? ' …' : ''}`,
        duration: 10000,
      })
      return
    }

    const updated = await Promise.all(
      changes.map(({ recovery, name, elution_volume, area }) =>
        recoveryApi.update(recovery.id, {
          name,
          study_id: recovery.study_id ?? null,
          recovery_set_id: recovery.recovery_set_id ?? null,
          contact_id: recovery.contact_id ?? null,
          surface_id: recovery.surface_id ?? null,
          sampling_method_id: recovery.sampling_method_id ?? null,
          extraction_method_id: recovery.extraction_method_id ?? null,
          experience_level_of_sampler_id: recovery.experience_level_of_sampler_id ?? null,
          elution_volume,
          area,
        }),
      ),
    )
    const updatedById = new Map(updated.map((recovery) => [recovery.id, recovery]))
    allRecoveries.value = allRecoveries.value.map((item) => updatedById.get(item.id) ?? item)
    toast.add({
      color: 'success',
      title: changes.length ? `Updated ${changes.length} recover${changes.length === 1 ? 'y' : 'ies'}` : 'No changes found',
    })
  } catch {
    toast.add({ color: 'error', title: 'Import failed', description: 'Could not read or save this file. Please try again.' })
  } finally {
    importing.value = false
  }
}

// -- Inline edit mode for the table --
// Name, elution volume and area become inputs on every row; each value is
// saved when its input loses focus.

const editMode = ref(false)
const savingRecoveryIds = ref<Set<string>>(new Set())

async function saveRecoveryField(
  row: Recovery,
  patch: Partial<Pick<RecoveryInput, 'name' | 'elution_volume' | 'area'>>,
) {
  const next = { ...row, ...patch }
  if (patch.name !== undefined && nameTaken(patch.name, row.id)) {
    loadError.value = `The name "${patch.name}" is already used by another recovery. Names must be unique.`
    return
  }
  loadError.value = ''
  if (
    next.name === row.name &&
    next.elution_volume === row.elution_volume &&
    next.area === row.area
  )
    return
  savingRecoveryIds.value = new Set(savingRecoveryIds.value).add(row.id)
  try {
    const updated = await recoveryApi.update(row.id, {
      name: next.name ?? null,
      study_id: row.study_id ?? null,
      recovery_set_id: row.recovery_set_id ?? null,
      contact_id: row.contact_id ?? null,
      surface_id: row.surface_id ?? null,
      sampling_method_id: row.sampling_method_id ?? null,
      extraction_method_id: row.extraction_method_id ?? null,
      experience_level_of_sampler_id: row.experience_level_of_sampler_id ?? null,
      elution_volume: next.elution_volume ?? null,
      area: next.area ?? null,
    })
    allRecoveries.value = allRecoveries.value.map((item) => (item.id === updated.id ? updated : item))
  } catch {
    loadError.value = 'Could not save this change. Please try again.'
  } finally {
    const after = new Set(savingRecoveryIds.value)
    after.delete(row.id)
    savingRecoveryIds.value = after
  }
}

const numberOrNull = (value: number | null | undefined) =>
  value == null || Number.isNaN(value) ? null : value

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

// Pre-fills the recovery set field with the user's own laboratory name so
// it's never left pointing at someone else's set by accident, while still
// letting them pick or create a different one.
const defaultRecoverySetName = computed(() => auth.user?.laboratory?.laboratory_name ?? null)

async function ensureDefaultRecoverySet(): Promise<string | null> {
  const name = defaultRecoverySetName.value
  if (!name) return null
  const existing = recoverySets.value.find((set) => set.name === name)
  if (existing) return existing.id
  const created = await createRecoverySet(name)
  onRecoverySetCreated(created)
  return created.id
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
      <div class="flex gap-2">
        <UButton type="button" icon="i-lucide-filter-x" variant="outline" size="sm" @click="clearFilters()">
          Clear Filters
        </UButton>
        <UButton
          type="button"
          :label="editMode ? 'Done' : 'Edit values'"
          :icon="editMode ? 'i-lucide-check' : 'i-lucide-pencil'"
          :variant="editMode ? 'solid' : 'outline'"
          size="sm"
          :disabled="!recoveries.length"
          @click="editMode = !editMode"
        />
        <div class="flex items-center gap-2 border border-default rounded-md px-2 py-1">
          <span class="text-xs font-medium text-muted">CSV</span>
          <UButton
            type="button"
            label="Download"
            icon="i-lucide-download"
            variant="outline"
            size="sm"
            :disabled="!recoveries.length"
            @click="onDownloadClick"
          />
          <UButton
            type="button"
            label="Upload"
            icon="i-lucide-upload"
            variant="outline"
            size="sm"
            :loading="importing"
            :disabled="!recoveries.length"
            @click="openImportDialog"
          />
        </div>
      </div>
      <UInput
        v-model="filters['global'].value"
        type="text"
        icon="i-lucide-search"
        placeholder="Keyword Search"
      />
    </div>

    <DataTableSkeleton v-if="loading" :columns="5" />

    <UAlert
      v-else-if="!groupedRecoveries.length"
      color="neutral"
      variant="outline"
      description="No recoveries yet."
    />

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
          paginator
          :rows="25"
          :rowsPerPageOptions="[25, 50, 100, 200]"
          filterDisplay="menu"
          :globalFilterFields="['extraction_method.extraction_protocol', 'elution_volume', 'area', 'scenarioNames']"
        >
          <Column header="Contact">
            <template #body="{ data }">{{ contactLabelFor(data.contact_id) }}</template>
          </Column>
          <Column header="Surface">
            <template #body="{ data }">{{ surfaceLabel(data.surface) }}</template>
          </Column>
          <Column header="Name">
            <template #body="{ data }">
              <UInput
                v-if="editMode"
                :model-value="data.name ?? ''"
                placeholder="Optional"
                class="w-full"
                @change="(event: Event) => saveRecoveryField(data, { name: (event.target as HTMLInputElement).value.trim() || null })"
              />
              <template v-else>{{ data.name || '—' }}</template>
            </template>
          </Column>
          <Column
          field="scenarioNames"
          header="Scenario"
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #body="{ data }"><ScenarioBadges :names="surfaceScenarios[data.surface_id] ?? []" /></template>
          <template #filter="{ filterModel }">
            <UInput v-model="filterModel.value" type="text" placeholder="Search by scenario" />
          </template>
        </Column>
          <Column header="Sampling method">
            <template #body="{ data }">{{ samplingMethodLabel(data.sampling_method) }}</template>
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
            <template #body="{ data }">
              <UInputNumber :min="0" :step="0.1" :step-snapping="false" :format-options="{ maximumFractionDigits: 6 }"
                v-if="editMode"
                :model-value="data.elution_volume ?? undefined"
                orientation="vertical"
                class="w-full min-w-32"
                @update:model-value="(value: number | null) => saveRecoveryField(data, { elution_volume: numberOrNull(value) })"
              />
              <template v-else>{{ data.elution_volume != null ? auth.formatNumber(data.elution_volume) : '—' }}</template>
            </template>
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
            <template #body="{ data }">
              <UInputNumber :min="0" :step="0.1" :step-snapping="false" :format-options="{ maximumFractionDigits: 6 }"
                v-if="editMode"
                :model-value="data.area ?? undefined"
                orientation="vertical"
                class="w-full min-w-32"
                @update:model-value="(value: number | null) => saveRecoveryField(data, { area: numberOrNull(value) })"
              />
              <template v-else>{{ data.area != null ? auth.formatNumber(data.area) : '—' }}</template>
            </template>
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
      :title="editingId !== null
        ? 'Edit recovery'
        : step === 1
          ? 'Add recovery - step 1 of 2'
          : `Add recovery - step 2 of 2: details for ${detailRows.length} new recover${detailRows.length === 1 ? 'y' : 'ies'}`"
      :ui="{ content: 'max-w-5xl', footer: 'justify-end' }"
    >
      <template #body>
        <div v-if="step === 1" class="flex flex-col gap-4">
          <UFormField
            v-if="editingId === null"
            label="Surfaces"
            hint="One recovery is created per selected surface"
          >
            <SurfaceMultiSelect
              v-model="surfaceIds"
              :study-id="props.studyId"
              :contacts="props.contacts"
              :contact-templates="contactTemplates"
              :scenarios="scenarios"
            />
          </UFormField>
          <template v-else>
            <EntitySelect
              v-model="surfaceId"
              label="Surface"
              :options="studySurfaces"
              :option-label="surfaceLabel"
              :error="errors.surface_id"
            />
            <UFormField label="Internal name" hint="Optional - helps tell otherwise identical recoveries apart">
              <UInput v-model="name" class="w-full" />
            </UFormField>
          </template>
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
            :option-label="samplingMethodLabel"
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
          <template v-if="editingId === null">
            <UFormField label="Name template" hint="Optional - you can adjust each name in the next step">
              <div class="flex flex-wrap items-center gap-2 mb-2">
                <span class="text-sm text-surface-500 dark:text-surface-400">Insert counter:</span>
                <UButton
                  v-for="token in [
                    { token: '{#}', example: '1, 2, 3 …' },
                    { token: '{##}', example: '01, 02, 03 …' },
                    { token: '{###}', example: '001, 002, 003 …' },
                  ]"
                  :key="token.token"
                  type="button"
                  size="xs"
                  color="primary"
                  variant="soft"
                  icon="i-lucide-plus"
                  :label="token.token"
                  :title="`Click to insert: ${token.example}`"
                  @click="insertTemplateToken(token.token)"
                />
              </div>
              <UInput ref="templateInput" v-model="nameTemplate" placeholder="e.g. Sample {##}" class="w-full" />
              <template #help>
                Recoveries are numbered in the order of the selected surfaces:
                <code>{#}</code> gives 1, 2, 3 …, <code>{##}</code> gives 01, 02, 03 …,
                <code>{###}</code> gives 001, 002, 003 …
              </template>
            </UFormField>
          </template>
          <template v-else>
            <UFormField label="Elution volume" :error="errors.elution_volume">
              <UFieldGroup>
                <UInputNumber :min="0" :step="0.1" :step-snapping="false" :format-options="{ maximumFractionDigits: 6 }" v-model="elutionVolume" orientation="vertical" class="w-full" />
                <UBadge color="neutral" variant="outline" size="lg" label="µL" />
              </UFieldGroup>
            </UFormField>
            <UFormField label="Area" :error="errors.area">
              <UFieldGroup>
                <UInputNumber :min="0" :step="0.1" :step-snapping="false" :format-options="{ maximumFractionDigits: 6 }" v-model="area" orientation="vertical" class="w-full" />
                <UBadge color="neutral" variant="outline" size="lg" label="cm²" />
              </UFieldGroup>
            </UFormField>
          </template>

          <UAlert v-if="submitError" color="error" variant="outline" :description="submitError" />
        </div>
        <div v-else class="flex flex-col gap-3">
          <p class="text-sm text-surface-500 dark:text-surface-400">
            Add a name, elution volume and area for each recovery, or leave them empty and fill them in later.
            Nothing is saved until you click Create.
          </p>
          <div class="flex justify-end">
            <UButton
              type="button"
              :label="bulkOpen ? 'Hide set for all' : 'Set values for all'"
              :icon="bulkOpen ? 'i-lucide-chevron-up' : 'i-lucide-list-checks'"
              variant="outline"
              size="sm"
              @click="bulkOpen = !bulkOpen"
            />
          </div>
          <div v-if="bulkOpen" class="flex flex-wrap items-end gap-3 border border-default rounded-md p-3">
            <UFormField label="Set elution volume for all" class="flex-1 min-w-48">
              <UFieldGroup class="w-full">
                <UInputNumber :min="0" :step="0.1" :step-snapping="false" :format-options="{ maximumFractionDigits: 6 }" v-model="bulkElutionVolume" orientation="vertical" class="w-full" />
                <UBadge color="neutral" variant="outline" size="lg" label="µL" />
              </UFieldGroup>
            </UFormField>
            <UFormField label="Set area for all" class="flex-1 min-w-48">
              <UFieldGroup class="w-full">
                <UInputNumber :min="0" :step="0.1" :step-snapping="false" :format-options="{ maximumFractionDigits: 6 }" v-model="bulkArea" orientation="vertical" class="w-full" />
                <UBadge color="neutral" variant="outline" size="lg" label="cm²" />
              </UFieldGroup>
            </UFormField>
            <UButton
              label="Apply to all"
              icon="i-lucide-copy-check"
              variant="outline"
              :disabled="bulkElutionVolume == null && bulkArea == null"
              @click="applyToAllRows"
            />
          </div>

          <div class="overflow-x-auto">
            <DataTable :value="detailRows" data-key="key" scrollable scroll-height="28rem">
              <Column header="Contact">
                <template #body="{ data }">{{ contactLabelFor(data.contactId) }}</template>
              </Column>
              <Column header="Surface">
                <template #body="{ data }">{{ surfaceEntryLabel(data.surfaceId) }}</template>
              </Column>
              <Column header="Name" style="min-width: 12rem">
                <template #body="{ data }">
                  <UInput
                    v-model="data.name"
                    placeholder="Optional"
                    class="w-full"
                    :color="duplicateRowNames.has(data.key) ? 'error' : undefined"
                    :highlight="duplicateRowNames.has(data.key)"
                  />
                </template>
              </Column>
              <Column header="Elution volume (µL)" style="min-width: 10rem">
                <template #body="{ data }">
                  <UInputNumber :min="0" :step="0.1" :step-snapping="false" :format-options="{ maximumFractionDigits: 6 }" v-model="data.elutionVolume" orientation="vertical" class="w-full" />
                </template>
              </Column>
              <Column header="Area (cm²)" style="min-width: 10rem">
                <template #body="{ data }">
                  <UInputNumber :min="0" :step="0.1" :step-snapping="false" :format-options="{ maximumFractionDigits: 6 }" v-model="data.area" orientation="vertical" class="w-full" />
                </template>
              </Column>
            </DataTable>
          </div>
          <UAlert
            v-if="duplicateRowNames.size"
            color="error"
            variant="outline"
            :description="`${duplicateRowNames.size} recovery name${duplicateRowNames.size === 1 ? ' is' : 's are'} not unique (marked in red). Names must be unique within the study.`"
          />
          <UAlert v-if="submitError" color="error" variant="outline" :description="submitError" />
        </div>
      </template>
      <template #footer>
        <UButton
          v-if="step === 2"
          label="Back"
          icon="i-lucide-arrow-left"
          variant="ghost"
          class="mr-auto"
          @click="step = 1"
        />
        <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="dialogVisible = false" />
        <UButton
          v-if="editingId !== null"
          label="Save"
          icon="i-lucide-save"
          :loading="submitting"
          @click="submitForm"
        />
        <UButton
          v-else-if="step === 1"
          label="Next"
          trailing-icon="i-lucide-arrow-right"
          :disabled="!canSave"
          @click="submitForm"
        />
        <UButton
          v-else
          :label="detailRows.length > 1 ? `Create ${detailRows.length} recoveries` : 'Create'"
          icon="i-lucide-save"
          :loading="submitting"
          :disabled="!detailRows.length || duplicateRowNames.size > 0"
          @click="createRecoveries"
        />
      </template>
    </UModal>


    <UModal
      v-model:open="importDialogVisible"
      title="Upload CSV"
      :ui="{ content: 'max-w-md', footer: 'justify-end' }"
    >
      <template #body>
        <div class="flex flex-col gap-4">
          <p class="text-sm text-surface-500 dark:text-surface-400">
            Upload a file downloaded from this table. The columns name, elution_volume_ul and area_cm2 will replace
            the current values. The id and info_* columns are not changed.
          </p>
          <UFileUpload
            v-model="pendingCsvFile"
            accept=".csv,text/csv"
            label="Drop your CSV file here"
            description="or click to choose a file"
            icon="i-lucide-file-spreadsheet"
            class="w-full min-h-32"
          />
          <URadioGroup
            v-model="decimalSeparator"
            legend="Decimal separator used in the file"
            :items="decimalOptions"
          />
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="importDialogVisible = false" />
        <UButton label="Import" icon="i-lucide-upload" :disabled="!pendingCsvFile" @click="importCsv" />
      </template>
    </UModal>

    <UModal
      v-model:open="csvHintVisible"
      title="Editing the CSV file"
      :ui="{ content: 'max-w-lg', footer: 'justify-end' }"
    >
      <template #body>
        <div class="flex flex-col gap-4 text-sm">
          <p>
            Edit the file in a spreadsheet and upload it again with <strong>Upload CSV</strong> to update the
            recoveries.
          </p>
          <ul class="flex flex-col gap-2 list-disc pl-5">
            <li>
              <strong>You may edit:</strong> <code>name</code>, <code>elution_volume_ul</code> and
              <code>area_cm2</code>. Names must be unique within the study.
            </li>
            <li>
              <strong>Do not edit:</strong> <code>id_do_not_edit</code>. It tells the upload which recovery a row
              belongs to, so don't change, delete or duplicate it, and don't add rows.
            </li>
            <li>
              <strong>Information only:</strong> <code>info_scenario</code>, <code>info_contact</code>, <code>info_surface</code>
              and <code>info_recovery_set</code>. Changes to these columns are ignored.
            </li>
          </ul>
          <p>Downloaded files always use a point as decimal separator (for example 1.5). When uploading you choose the decimal separator your file uses (point or comma); it defaults to your profile's number format.</p>
          <UCheckbox v-model="csvHintDontShowAgain" label="Don't show this again" />
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="csvHintVisible = false" />
        <UButton label="Download CSV" icon="i-lucide-download" @click="confirmCsvDownload" />
      </template>
    </UModal>
  </div>
</template>
