<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import ContextMenu from 'openvue/contextmenu'
import { FilterMatchMode } from '@openvue/core/api'
import type { TabsItem } from '@nuxt/ui'
import type { MenuItem } from 'openvue/menuitem'
import ScenarioBadges from '@/components/data/ScenarioBadges.vue'
import ContactChains from '@/components/data/ContactChains.vue'
import type { LinkOp } from '@/components/data/ContactChains.vue'
import ContactInstanceDialog from '@/components/data/ContactInstanceDialog.vue'
import IndividualsPanel from '@/components/data/IndividualsPanel.vue'
import ItemsPanel from '@/components/data/ItemsPanel.vue'
import SamplesPanel from '@/components/data/SamplesPanel.vue'
import ResultsTab from '@/components/scenarios/ResultsTab.vue'
import type { ContactChainInfo } from '@/components/data/ContactChainNode.vue'
import { templateName, surfaceInstanceIcon, surfaceInstanceDetail } from '@/components/data/contactTemplateLabel'
import { useIndividualOptions } from '@/components/scenarios/individualOptions'
import { useConfirm } from '@/composables/useConfirm'
import { canEnterStudyData, provideStudyReadOnly, useStudyReadOnly } from '@/composables/useStudyAccess'
import { useAuthStore } from '@/stores/auth'
import { useTourStore } from '@/stores/tour'
import { listScenarios } from '@/api/scenarios'
import { useToast } from '@nuxt/ui/composables'
import {
  getStudy,
  planningSheetErrors,
  planningSheetConfirmation,
  uploadPlanningSheet,
  type PlanningSheetConfirmation,
} from '@/api/studies'
import { getErrorMessage } from '@/api/errors'
import { listContacts, deleteContact, updateContact } from '@/api/contacts'
import type { Contact, ContactTemplate, Sample, Scenario } from '@/api/types'

const confirm = useConfirm()
const route = useRoute()
const router = useRouter()

const props = defineProps<{ studyId: string }>()

// Other laboratories' studies can be browsed but not changed. Inside the
// study page the flag is provided; on the standalone data route this view
// works it out from the study itself and passes it on to its panels.
const auth = useAuthStore()
const providedReadOnly = useStudyReadOnly()
const ownStudy = ref<boolean | null>(null)
const readOnly = computed(() => providedReadOnly.value || ownStudy.value === false)
provideStudyReadOnly(readOnly)

const studyId = computed(() => props.studyId)

const {
  individuals,
  describeIndividual,
  individualName,
  load: reloadIndividuals,
} = useIndividualOptions(props.studyId)

const loading = ref(false)
const loadError = ref('')

const studyScenarios = ref<Scenario[]>([])
const studyTitle = ref<string | null>(null)
const contactTemplates = ref<ContactTemplate[]>([])
const contacts = ref<Contact[]>([])
const scopedSamples = ref<Sample[]>([])

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    // The title only names exported files, so a failure here must not block loading.
    getStudy(studyId.value)
      .then((study) => {
        studyTitle.value = study.title ?? null
        ownStudy.value = canEnterStudyData(study, auth.user)
      })
      .catch(() => {})
    const [scenariosOfStudy, studyContacts] = await Promise.all([
      listScenarios(studyId.value),
      listContacts(studyId.value),
    ])
    studyScenarios.value = scenariosOfStudy
    const templates = scenariosOfStudy.flatMap((scenario) => scenario.contact_templates)
    contactTemplates.value = templates

    // The study filter also returns contacts that only involve the study's
    // individuals; this page lists the ones of its scenarios' templates.
    const templateIds = new Set(templates.map((t) => t.id))
    contacts.value = studyContacts.filter(
      (contact) => contact.contact_template_id != null && templateIds.has(contact.contact_template_id),
    )
  } catch {
    loadError.value = 'Could not load data for this study.'
  } finally {
    loading.value = false
  }
}

// -- Planning sheet upload --
// The Excel planning checklist has sheets for individuals and items; uploading
// it creates/updates them here. The server checks every row first and rejects
// the whole file if any row is invalid, listing the problems.
const toast = useToast()
const planningSheetVisible = ref(false)
const planningSheetFile = ref<File | null>(null)
const planningSheetUploading = ref(false)
const planningSheetProblems = ref<string[]>([])
const planningSheetError = ref('')
// Set when the user has to decide something before the file is saved:
// new item categories to confirm (checking for typos before they land in the
// shared catalog) and/or scenarios for rows that have none - e.g. because the
// sheet was filled in before the scenarios were planned.
const pendingConfirmation = ref<PlanningSheetConfirmation | null>(null)
const assignScenarioIds = ref<string[]>([])

const pendingNewCategoryCount = computed(
  () =>
    (pendingConfirmation.value?.new_categories.length ?? 0) +
    (pendingConfirmation.value?.new_subcategories.length ?? 0),
)
const pendingUnassigned = computed(() => {
  const pending = pendingConfirmation.value
  if (!pending) return null
  const parts = []
  if (pending.unassigned_individuals)
    parts.push(`${pending.unassigned_individuals} individual${pending.unassigned_individuals === 1 ? '' : 's'}`)
  if (pending.unassigned_items) parts.push(`${pending.unassigned_items} item${pending.unassigned_items === 1 ? '' : 's'}`)
  return parts.length ? parts.join(' and ') : null
})
const scenarioAssignOptions = computed(() =>
  studyScenarios.value.map((scenario) => ({ label: scenario.name, value: scenario.id })),
)
const uploadBlocked = computed(
  () => !planningSheetFile.value || (!!pendingUnassigned.value && !assignScenarioIds.value.length),
)
// Bumped after an upload so the individuals and items panels load again.
const panelsKey = ref(0)

function openPlanningSheetUpload() {
  planningSheetFile.value = null
  planningSheetProblems.value = []
  planningSheetError.value = ''
  pendingConfirmation.value = null
  assignScenarioIds.value = []
  planningSheetVisible.value = true
}

watch(planningSheetFile, () => {
  planningSheetProblems.value = []
  planningSheetError.value = ''
  pendingConfirmation.value = null
  assignScenarioIds.value = []
})

function countText(created: number, updated: number, noun: string): string | null {
  const parts = []
  if (created) parts.push(`${created} added`)
  if (updated) parts.push(`${updated} updated`)
  return parts.length ? `${noun}: ${parts.join(', ')}` : null
}

async function runPlanningSheetUpload() {
  const file = planningSheetFile.value
  if (!file) return
  const options = {
    createCategories: pendingNewCategoryCount.value > 0,
    scenarioIds: pendingUnassigned.value ? assignScenarioIds.value : undefined,
  }
  planningSheetUploading.value = true
  planningSheetProblems.value = []
  planningSheetError.value = ''
  pendingConfirmation.value = null
  try {
    const result = await uploadPlanningSheet(props.studyId, file, options)
    planningSheetVisible.value = false
    individualCountOverride.value = null
    panelsKey.value++
    await Promise.all([reloadIndividuals(), load()])
    const summary = [
      countText(result.individuals_created, result.individuals_updated, 'Individuals'),
      countText(result.items_created, result.items_updated, 'Items'),
      countText(result.categories_created + result.subcategories_created, 0, 'New categories'),
    ].filter(Boolean)
    toast.add({
      color: 'success',
      title: 'Planning sheet uploaded',
      description: summary.length ? summary.join(' · ') : 'The file had no individuals or items.',
    })
  } catch (err) {
    pendingConfirmation.value = planningSheetConfirmation(err)
    if (pendingConfirmation.value) return
    planningSheetProblems.value = planningSheetErrors(err)
    if (!planningSheetProblems.value.length) {
      planningSheetError.value = getErrorMessage(err, 'Could not upload this file. Please try again.')
    }
  } finally {
    planningSheetUploading.value = false
  }
}

// First time entering data: hand over from the new-study guide (if it led
// here) to the data-entry guide. Waits for the study so read-only studies of
// other laboratories are known.
const tour = useTourStore()
onMounted(async () => {
  await load()
  if (readOnly.value || loadError.value) return
  if (tour.tourId === 'new-study') await tour.finish()
  tour.start('data-entry')
})

const dialogVisible = ref(false)
const editingNames = ref(false)

// Expand every group when entering edit-names mode, so the inputs this
// mode adds to each group's member table are actually visible right away
// instead of requiring each group to be expanded by hand first.
watch(editingNames, (isEditing) => {
  if (!isEditing) return
  expandedContactRows.value = Object.fromEntries(contactGroups.value.map((group) => [group.key, true]))
})

function onContactSaved(newContacts: Contact[]) {
  contacts.value = [...contacts.value, ...newContacts]
}

function contactTemplateFor(contact: Contact): ContactTemplate | null {
  return contactTemplates.value.find((t) => t.id === contact.contact_template_id) ?? null
}

// Which surface slot ('donor_surface' | 'recipient_surface') holds the item,
// for contact templates shaped item-on-one-side/individual-on-the-other.
// Mirrors ContactInstanceDialog's batching rule: only applies when exactly
// one side is an item.
function itemSideOf(template: ContactTemplate): 'donor_surface' | 'recipient_surface' | null {
  const donorIsItem = !!template.donor_surface_template?.item_id
  const recipientIsItem = !!template.recipient_surface_template?.item_id
  if (donorIsItem && !recipientIsItem) return 'donor_surface'
  if (recipientIsItem && !donorIsItem) return 'recipient_surface'
  return null
}

// -- Scenario scope --
// 'all' shows everything recorded for the study; picking a scenario narrows
// every tab to that scenario. Contacts belong to a scenario through their
// contact template; samples and results follow their contact.

const selectedScenarioId = computed<string | null>({
  get() {
    const id = route.query.scenario
    return typeof id === 'string' && studyScenarios.value.some((s) => s.id === id) ? id : null
  },
  set(value) {
    const { scenario: _drop, ...rest } = route.query
    router.replace({ query: value ? { ...rest, scenario: value } : rest })
  },
})

const scenarioOptions = computed(() => [
  { label: 'All data', value: 'all' },
  ...studyScenarios.value.map((scenario) => ({ label: scenario.name, value: scenario.id })),
])

const scenarioSelectValue = computed({
  get: () => selectedScenarioId.value ?? 'all',
  set: (value: string) => {
    selectedScenarioId.value = value === 'all' ? null : value
  },
})

// Base name for downloaded files: study title plus the selected scenario.
const exportName = computed(() => {
  const slug = (text: string) =>
    text
      .normalize('NFKD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 40)
  const study = slug(studyTitle.value ?? '') || `study-${studyId.value.slice(0, 8)}`
  const scenario = studyScenarios.value.find((s) => s.id === selectedScenarioId.value)
  return [study, scenario ? slug(scenario.name) : ''].filter(Boolean).join('_')
})

const visibleTemplates = computed<ContactTemplate[]>(() => {
  if (selectedScenarioId.value === null) return contactTemplates.value
  return (
    studyScenarios.value.find((s) => s.id === selectedScenarioId.value)?.contact_templates ?? []
  )
})

// Scenario names a contact belongs to, via its template; samples and
// results inherit them through the contact surface they were taken from.
function contactScenarioNames(contact: Contact): string[] {
  return studyScenarios.value
    .filter((s) => s.contact_templates.some((t) => t.id === contact.contact_template_id))
    .map((s) => s.name)
}

const surfaceScenarios = computed<Record<string, string[]>>(() => {
  const map: Record<string, Set<string>> = {}
  for (const contact of contacts.value) {
    const names = contactScenarioNames(contact)
    for (const surface of [contact.donor_surface, contact.recipient_surface]) {
      if (!surface) continue
      for (const name of names) (map[surface.id] ??= new Set()).add(name)
    }
  }
  return Object.fromEntries(Object.entries(map).map(([id, names]) => [id, [...names]]))
})

const visibleContacts = computed<Contact[]>(() => {
  if (selectedScenarioId.value === null) return contacts.value
  const templateIds = new Set(visibleTemplates.value.map((t) => t.id))
  return contacts.value.filter(
    (contact) => contact.contact_template_id != null && templateIds.has(contact.contact_template_id),
  )
})

interface ContactGroup {
  key: string
  template: ContactTemplate | null
  itemSide: 'donor_surface' | 'recipient_surface' | null
  itemSurfaceId: string | null
  members: Contact[]
  scenarioNames: string
}

// Contacts sharing the same template and the same item-side surface
// instance (i.e. the same batch-created item-to-many-individuals entry) are
// grouped into one expandable row, so the table doesn't repeat the item's
// details once per individual.
const contactGroups = computed<ContactGroup[]>(() => {
  const groups = new Map<string, ContactGroup>()
  for (const contact of visibleContacts.value) {
    const template = contactTemplateFor(contact)
    const itemSide = template ? itemSideOf(template) : null
    const itemSurfaceId = itemSide ? contact[itemSide]?.id ?? null : null
    const key = itemSide
      ? `${contact.contact_template_id}::${itemSurfaceId}`
      : `single::${contact.id}`

    const existing = groups.get(key)
    if (existing) {
      existing.members.push(contact)
    } else {
      groups.set(key, {
        key,
        template,
        itemSide,
        itemSurfaceId,
        members: [contact],
        scenarioNames: '',
      })
    }
  }
  return [...groups.values()].map((group) => ({
    ...group,
    scenarioNames: [...new Set(group.members.flatMap(contactScenarioNames))].join(', '),
  }))
})

// Icon + text for one side ('donor_surface' | 'recipient_surface') of a
// single contact, using the individual's position label when that side
// holds an individual rather than an item.
function sideDisplay(contact: Contact, side: 'donor_surface' | 'recipient_surface') {
  const surface = contact[side]
  const label = surface?.individual
    ? describeIndividual(surface.individual)
    : surfaceInstanceDetail(surface)
  return { icon: surfaceInstanceIcon(surface), label }
}

// Variants of sideDisplay for the expanded member table, which shows sex/age
// as separate badges next to the individual's name instead of baked into one
// string (describeIndividual's "Name (sex, age)") - they're already visible
// elsewhere on the row, no need to repeat them in prose form too.
function sideIcon(contact: Contact, side: 'donor_surface' | 'recipient_surface'): string | null {
  return surfaceInstanceIcon(contact[side])
}

function sideIndividual(contact: Contact, side: 'donor_surface' | 'recipient_surface') {
  return contact[side]?.individual ?? null
}

function sideIndividualLabel(contact: Contact, side: 'donor_surface' | 'recipient_surface'): string | null {
  const individual = sideIndividual(contact, side)
  return individual ? individualName(individual) : null
}

// Donor/Recipient column display for a group row: the fixed item side
// shows the item once; the individual side shows either the single
// individual (ungrouped contact) or a count badge (batch group).
function groupSideDisplay(group: ContactGroup, side: 'donor_surface' | 'recipient_surface') {
  const first = group.members[0]
  if (!first) return { icon: null, label: '—' }
  if (group.itemSide === side || group.members.length === 1) {
    return sideDisplay(first, side)
  }
  return { icon: 'i-lucide-users', label: `${group.members.length} individuals` }
}

// The individual behind a group member row, for the expansion table's
// separate Individual/Sex/Age columns - plain text crammed into one string
// ("Individual 2 (female, 26y)") is harder to scan than a name plus badges.
function memberIndividual(contact: Contact, itemSide: 'donor_surface' | 'recipient_surface' | null) {
  const side = itemSide === 'donor_surface' ? 'recipient_surface' : 'donor_surface'
  return contact[side]?.individual ?? null
}

async function deleteContacts(ids: string[]) {
  await Promise.all(ids.map((id) => deleteContact(id)))
  const removed = new Set(ids)
  contacts.value = contacts.value.filter((c) => !removed.has(c.id))
}

function confirmDeleteContact(contact: Contact) {
  confirm.require({
    message: 'Delete this contact? This cannot be undone.',
    header: 'Delete contact',
    rejectLabel: 'Cancel',
    acceptLabel: 'Delete',
    acceptColor: 'error',
    accept: () => deleteContacts([contact.id]),
  })
}

// -- Chain link --

// Applies link operations in order, updating the list optimistically. The
// inverse (in reverse order) is pushed onto the undo stack, so changing one
// link never means redoing a whole chain. A failed step rolls back the ones
// before it.
const chainUndoStack = ref<LinkOp[][]>([])

async function applyLinkOps(ops: LinkOp[], recordUndo = true) {
  const done: LinkOp[] = []
  try {
    for (const op of ops) {
      const contact = contacts.value.find((c) => c.id === op.contactId)
      if (!contact || (contact.previous_contact_id ?? null) === op.previousId) continue
      const before = contact.previous_contact_id ?? null
      await updateContact(op.contactId, { previous_contact_id: op.previousId })
      contact.previous_contact_id = op.previousId
      done.push({ contactId: op.contactId, previousId: before })
    }
  } catch {
    await applyLinkOps(done.reverse(), false)
    return
  }
  if (recordUndo && done.length) chainUndoStack.value.push(done.reverse())
}

async function undoChainChange() {
  const ops = chainUndoStack.value.pop()
  if (ops) await applyLinkOps(ops, false)
}

const chainDialogVisible = ref(false)
const chainingContact = ref<Contact | null>(null)
const chainValue = ref('__none__')
const chaining = ref(false)

// Contacts this one may follow: those of the template its own template follows.
const chainCandidates = computed<Contact[]>(() => {
  const previousTemplateId = chainingContact.value
    ? contactTemplateFor(chainingContact.value)?.previous_contact_template_id
    : null
  if (!previousTemplateId) return []
  const own = chainingContact.value
  const followed = new Set(
    contacts.value.filter((c) => c.id !== own?.id).map((c) => c.previous_contact_id),
  )
  return contacts.value.filter(
    (c) => c.contact_template_id === previousTemplateId && !followed.has(c.id),
  )
})

const chainItems = computed(() => [
  { label: 'None (first in chain)', value: '__none__' },
  ...chainCandidates.value.map((c) => ({ label: contactLabel(c), value: c.id })),
])

function canChain(contact: Contact): boolean {
  return !!contactTemplateFor(contact)?.previous_contact_template_id
}

function openChainDialog(contact: Contact) {
  chainingContact.value = contact
  chainValue.value = contact.previous_contact_id ?? '__none__'
  chainDialogVisible.value = true
}

async function saveChain() {
  const contact = chainingContact.value
  if (!contact) return
  chaining.value = true
  try {
    const previousId = chainValue.value === '__none__' ? null : chainValue.value
    await updateContact(contact.id, { previous_contact_id: previousId })
    contact.previous_contact_id = previousId
    chainDialogVisible.value = false
  } finally {
    chaining.value = false
  }
}

// -- Rename contact --

const renameDialogVisible = ref(false)
const renamingContact = ref<Contact | null>(null)
const renameValue = ref('')
const renaming = ref(false)

function openRenameDialog(contact: Contact) {
  renamingContact.value = contact
  renameValue.value = contact.name ?? ''
  renameDialogVisible.value = true
}

// Patches a contact's name on the existing object in place, rather than
// replacing `contacts.value` with a new array/objects - contactGroups
// rebuilds group.members from contacts.value on every change, so swapping
// in fresh object references on every rename made rows visibly reorder
// mid-edit (the table's row identity depends on these objects staying the
// same instance, not just the same id).
function patchContactName(id: string, name: string | null) {
  const contact = contacts.value.find((c) => c.id === id)
  if (contact) contact.name = name
}

// Unnamed contacts are numbered by their position across all of this
// study's contacts (not just within their group), so a given contact's
// number stays meaningful and doesn't shift just because a different group
// gets expanded or collapsed.
function contactFallbackName(contact: Contact): string {
  const position = contacts.value.findIndex((c) => c.id === contact.id)
  return `Contact ${position + 1}`
}

// Label used wherever a single contact must be picked or shown by itself.
function contactLabel(contact: Contact): string {
  const donor = sideDisplay(contact, 'donor_surface').label
  const recipient = sideDisplay(contact, 'recipient_surface').label
  return `${contact.name || contactFallbackName(contact)} (${donor} → ${recipient})`
}

function contactChainInfo(contact: Contact): ContactChainInfo {
  const template = contactTemplateFor(contact)
  return {
    title: contact.name || contactFallbackName(contact),
    templateName: template ? templateName(template) : '—',
    donor: sideDisplay(contact, 'donor_surface'),
    recipient: sideDisplay(contact, 'recipient_surface'),
  }
}

// Kept in the URL (?view=chains) so a reload stays on the same view.
const contactsView = computed<'list' | 'chains'>({
  get() {
    // Chaining only edits, so read-only always shows the list.
    if (readOnly.value) return 'list'
    return route.query.view === 'chains' ? 'chains' : 'list'
  },
  set(value) {
    const { view: _drop, ...rest } = route.query
    router.replace({ query: value === 'chains' ? { ...rest, view: 'chains' } : rest })
  },
})
const contactsViewItems = [
  { label: 'List', value: 'list', icon: 'i-lucide-list' },
  { label: 'Chains', value: 'chains', icon: 'i-lucide-link' },
]

// Edit-names mode keeps every row's input mounted at once (so several
// contacts can be renamed in one pass without re-opening anything per row),
// bypassing PrimeVue's single-row cell-edit machinery entirely.
const pendingMemberNames = new Map<string, string>()

function onMemberNameInput(contact: Contact, value: string) {
  pendingMemberNames.set(contact.id, value)
}

async function onMemberNameBlur(contact: Contact) {
  const pending = pendingMemberNames.get(contact.id)
  pendingMemberNames.delete(contact.id)
  if (pending === undefined) return
  const trimmed = pending.trim() || null
  if (trimmed === (contact.name ?? null)) return
  await updateContact(contact.id, { name: trimmed })
  patchContactName(contact.id, trimmed)
}

async function saveRename() {
  if (!renamingContact.value) return
  renaming.value = true
  try {
    const name = renameValue.value.trim() || null
    await updateContact(renamingContact.value.id, { name })
    patchContactName(renamingContact.value.id, name)
    renameDialogVisible.value = false
  } finally {
    renaming.value = false
  }
}

// Inline cell edit on the expanded member table's Name column - a quicker
// path to the same rename than opening the dialog, for renaming several
// contacts in a row.
async function onMemberNameEditComplete(event: { data: Contact; newValue: string; field: string }) {
  const trimmed = event.newValue.trim() || null
  if (trimmed === (event.data.name ?? null)) return
  await updateContact(event.data.id, { name: trimmed })
  patchContactName(event.data.id, trimmed)
}

function confirmDeleteGroup(group: ContactGroup) {
  const count = group.members.length
  confirm.require({
    message:
      count > 1
        ? `Delete all ${count} contacts in this group? This cannot be undone.`
        : 'Delete this contact? This cannot be undone.',
    header: count > 1 ? `Delete ${count} contacts` : 'Delete contact',
    rejectLabel: 'Cancel',
    acceptLabel: 'Delete',
    acceptColor: 'error',
    accept: () => deleteContacts(group.members.map((c) => c.id)),
  })
}

// -- Context menu --

const contactContextMenu = ref<InstanceType<typeof ContextMenu>>()
const contextMenuGroup = ref<ContactGroup>()
const contextMenuContact = ref<Contact>()

const groupContextMenuItems = computed<MenuItem[]>(() => {
  const group = contextMenuGroup.value
  if (!group) return []
  const items: MenuItem[] = []
  if (group.members.length === 1) {
    items.push({
      label: 'Rename',
      icon: 'i-lucide-pencil',
      command: () => openRenameDialog(group.members[0]!),
    })
    if (canChain(group.members[0]!)) {
      items.push({
        label: 'Set previous contact',
        icon: 'i-lucide-link',
        command: () => openChainDialog(group.members[0]!),
      })
    }
  }
  items.push({
    label: group.members.length > 1 ? `Delete all ${group.members.length} contacts` : 'Delete',
    icon: 'i-lucide-trash-2',
    command: () => confirmDeleteGroup(group),
  })
  return items
})

const memberContextMenuItems = computed<MenuItem[]>(() => {
  const contact = contextMenuContact.value
  if (!contact) return []
  return [
    {
      label: 'Rename',
      icon: 'i-lucide-pencil',
      command: () => openRenameDialog(contact),
    },
    ...(canChain(contact)
      ? [{ label: 'Set previous contact', icon: 'i-lucide-link', command: () => openChainDialog(contact) }]
      : []),
    {
      label: 'Delete',
      icon: 'i-lucide-trash-2',
      command: () => confirmDeleteContact(contact),
    },
  ]
})

function openGroupContextMenu(event: Event, group: ContactGroup) {
  if (readOnly.value) return
  contextMenuContact.value = undefined
  contextMenuGroup.value = group
  contactContextMenu.value?.show(event)
}

function openMemberContextMenu(event: Event, contact: Contact) {
  if (readOnly.value) return
  contextMenuGroup.value = undefined
  contextMenuContact.value = contact
  contactContextMenu.value?.show(event)
}

function onGroupRowContextMenu(event: { originalEvent: Event; data: ContactGroup }) {
  openGroupContextMenu(event.originalEvent, event.data)
}

const expandedContactRows = ref<Record<string, boolean>>({})

function initContactFilters() {
  return {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
    scenarioNames: { value: null, matchMode: FilterMatchMode.CONTAINS },
  }
}

const contactFilters = ref(initContactFilters())

function clearContactFilters() {
  contactFilters.value = initContactFilters()
}

// Panel edits override the initially loaded count.
const individualCountOverride = ref<number | null>(null)
const individualCount = computed(() => individualCountOverride.value ?? individuals.value.length)

const itemCount = ref(0)

const tabItems = computed<TabsItem[]>(() => [
  { label: 'Individuals', value: 'individuals', slot: 'individuals', badge: individualCount.value },
  { label: 'Items', value: 'items', slot: 'items', badge: itemCount.value },
  { label: 'Contacts', value: 'contacts', slot: 'contacts', badge: visibleContacts.value.length },
  { label: 'Samples', value: 'samples', slot: 'samples', badge: scopedSamples.value.length },
  { label: 'Results', value: 'results', slot: 'results' },
])

const tabValues = new Set(['individuals', 'items', 'contacts', 'samples', 'results'])

const activeTab = computed<string>({
  get() {
    const tab = route.query.tab
    return typeof tab === 'string' && tabValues.has(tab) ? tab : 'individuals'
  },
  set(value) {
    router.replace({ query: { ...route.query, tab: value } })
  },
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-between gap-3">
      <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">{{ readOnly ? 'Data' : 'Data entry' }}</h1>
      <div class="flex items-center gap-2">
      <UButton
        v-if="!readOnly"
        label="Upload planning sheet"
        icon="i-lucide-file-up"
        color="neutral"
        variant="outline"
        @click="openPlanningSheetUpload"
      />
      <UButton
        v-if="!readOnly"
        label="Guide me"
        icon="i-lucide-circle-help"
        color="neutral"
        variant="ghost"
        @click="tour.start('data-entry', { force: true })"
      />
      </div>
    </div>

    <UModal
      v-model:open="planningSheetVisible"
      title="Upload planning sheet"
      :ui="{ content: 'max-w-lg', footer: 'justify-end' }"
    >
      <template #body>
        <div class="flex flex-col gap-4">
          <p class="text-sm text-surface-500 dark:text-surface-400">
            Upload the Excel planning checklist with the individuals and items you filled in. Rows with an ID update
            existing entries, rows without an ID are added. Rows you removed from the file are not deleted here.
          </p>
          <UFileUpload
            v-model="planningSheetFile"
            accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            label="Drop your planning sheet here"
            description="or click to choose an .xlsx file"
            icon="i-lucide-file-spreadsheet"
            class="w-full min-h-32"
          />
          <UAlert v-if="planningSheetError" color="error" variant="subtle" :description="planningSheetError" />
          <UAlert
            v-if="pendingNewCategoryCount"
            color="warning"
            variant="subtle"
            icon="i-lucide-folder-plus"
            title="This file adds new item categories"
          >
            <template #description>
              <p class="mb-2">
                They will be added to the shared catalog for all studies. Check them for typos - if one should be an
                existing category, fix it in the file and upload it again.
              </p>
              <ul class="list-disc pl-4 max-h-48 overflow-y-auto">
                <li v-for="name in pendingConfirmation?.new_categories" :key="`c-${name}`">
                  Category: <span class="font-medium">{{ name }}</span>
                </li>
                <li
                  v-for="sub in pendingConfirmation?.new_subcategories"
                  :key="`s-${sub.category}-${sub.name}`"
                >
                  Subcategory: <span class="font-medium">{{ sub.name }}</span> (in {{ sub.category }})
                </li>
              </ul>
            </template>
          </UAlert>
          <template v-if="pendingUnassigned">
            <UAlert
              v-if="!studyScenarios.length"
              color="warning"
              variant="subtle"
              icon="i-lucide-route"
              title="Plan a scenario first"
              :description="`${pendingUnassigned} in this file have no scenario, and this study has no scenarios yet. Plan at least one scenario in the planning step, then upload the file again.`"
            />
            <UFormField
              v-else
              label="Scenarios for rows without a scenario"
              :description="`${pendingUnassigned} in this file have no scenario. Every individual and item needs one - choose which scenarios they belong to.`"
              required
            >
              <USelectMenu
                v-model="assignScenarioIds"
                :items="scenarioAssignOptions"
                value-key="value"
                multiple
                placeholder="Choose scenarios"
                clear
                class="w-full"
              />
            </UFormField>
          </template>
          <UAlert
            v-if="planningSheetProblems.length"
            color="error"
            variant="subtle"
            title="Nothing was saved. Please fix these rows and upload the file again:"
          >
            <template #description>
              <ul class="list-disc pl-4 max-h-48 overflow-y-auto">
                <li v-for="problem in planningSheetProblems" :key="problem">{{ problem }}</li>
              </ul>
            </template>
          </UAlert>
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="planningSheetVisible = false" />
        <UButton
          :label="pendingConfirmation ? 'Confirm & upload' : 'Upload'"
          :icon="pendingConfirmation ? 'i-lucide-check' : 'i-lucide-upload'"
          :disabled="uploadBlocked"
          :loading="planningSheetUploading"
          @click="runPlanningSheetUpload"
        />
      </template>
    </UModal>

    <div v-if="loading" class="flex justify-center py-12">
      <UProgress class="w-12" />
    </div>

    <UAlert v-else-if="loadError" color="error" variant="outline" :description="loadError" />

    <div v-if="!loading && !loadError" class="flex flex-wrap items-end gap-3">
      <UFormField label="Scenario" data-tour="data-scenario" :hint="readOnly ? 'Choose a scenario to filter the data' : 'Choose a scenario to add data to it, or view all data'">
        <USelect v-model="scenarioSelectValue" :items="scenarioOptions" class="w-72" />
      </UFormField>
      <p v-if="!studyScenarios.length && !readOnly" class="text-sm text-warning pb-2">
        Plan a scenario for this study first.
      </p>
    </div>

    <UTabs v-if="!loading && !loadError" v-model="activeTab" data-tour="data-tabs" :items="tabItems" :unmount-on-hide="false" class="w-full">
      <template #individuals>
        <IndividualsPanel :key="`individuals-${panelsKey}`" :study-id="studyId" :scenarios="studyScenarios" :scenario-id="selectedScenarioId" @update:count="individualCountOverride = $event" />
      </template>

      <template #items>
        <ItemsPanel :key="`items-${panelsKey}`" :study-id="studyId" :contact-templates="visibleTemplates" :scenarios="studyScenarios" :scenario-id="selectedScenarioId" @update:count="itemCount = $event" />
      </template>

      <template #contacts>
        <div class="flex flex-col gap-4" data-tour="contacts-panel">
          <div class="flex items-center justify-between">
            <p class="text-sm text-surface-500 dark:text-surface-400">
              Actual contacts recorded for this study's planned scenarios.
            </p>
            <UButton
              v-if="!readOnly"
              data-tour="add-contact"
              label="Add actual contact"
              icon="i-lucide-plus"
              variant="outline"
              :disabled="!visibleTemplates.length"
              @click="dialogVisible = true"
            />
          </div>

          <UAlert
            v-if="!visibleTemplates.length && !readOnly"
            color="info"
            variant="outline"
            description="Plan a scenario with at least one contact template before entering actual data."
          />

          <UTabs
            v-if="!readOnly"
            v-model="contactsView"
            :items="contactsViewItems"
            :content="false"
            variant="pill"
            size="sm"
            class="w-fit"
          />

          <ContactChains
            v-if="contactsView === 'chains'"
            :contacts="visibleContacts"
            :contact-templates="visibleTemplates"
            :info="contactChainInfo"
            :can-undo="chainUndoStack.length > 0"
            @change="applyLinkOps"
            @undo="undoChainChange"
          />

          <div v-show="contactsView === 'list'" class="overflow-x-auto">
            <div class="mb-3 flex items-center justify-between gap-3">
              <div class="flex gap-2">
                <UButton
                  type="button"
                  icon="i-lucide-filter-x"
                  variant="outline"
                  size="sm"
                  @click="clearContactFilters()"
                >
                  Clear Filters
                </UButton>
                <UButton
                  v-if="!readOnly"
                  type="button"
                  :label="editingNames ? 'Done' : 'Edit names'"
                  :icon="editingNames ? 'i-lucide-check' : 'i-lucide-pencil'"
                  :variant="editingNames ? 'solid' : 'outline'"
                  size="sm"
                  :disabled="!visibleContacts.length"
                  @click="editingNames = !editingNames"
                />
              </div>
              <UInput
                v-model="contactFilters['global'].value"
                type="text"
                icon="i-lucide-search"
                placeholder="Keyword Search"
              />
            </div>

            <ContextMenu ref="contactContextMenu" :model="contextMenuGroup ? groupContextMenuItems : memberContextMenuItems" />

            <DataTable
              v-model:filters="contactFilters"
              v-model:expanded-rows="expandedContactRows"
              :value="contactGroups"
              data-key="key"
              paginator
              :rows="25"
              :rows-per-page-options="[25, 50, 100, 200]"
              filter-display="menu"
              :global-filter-fields="['template.name', 'scenarioNames']"
              :row-class="() => 'hover:bg-elevated'"
              @row-contextmenu="onGroupRowContextMenu"
            >
              <template #empty>No actual contacts recorded yet.</template>
              <Column expander style="width: 2.5rem" />
              <Column header="Contact template">
                <template #body="{ data }">{{ data.template ? templateName(data.template) : '—' }}</template>
              </Column>
              <Column header="Donor">
                <template #body="{ data }">
                  <span class="flex items-center gap-1.5">
                    <UIcon v-if="groupSideDisplay(data, 'donor_surface').icon" :name="groupSideDisplay(data, 'donor_surface').icon!" class="shrink-0" />
                    {{ groupSideDisplay(data, 'donor_surface').label }}
                  </span>
                </template>
              </Column>
              <Column header="Recipient">
                <template #body="{ data }">
                  <span class="flex items-center gap-1.5">
                    <UIcon v-if="groupSideDisplay(data, 'recipient_surface').icon" :name="groupSideDisplay(data, 'recipient_surface').icon!" class="shrink-0" />
                    {{ groupSideDisplay(data, 'recipient_surface').label }}
                  </span>
                </template>
              </Column>
              <Column
          field="scenarioNames"
          header="Scenario"
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #body="{ data }"><ScenarioBadges :names="[...new Set<string>(data.members.flatMap(contactScenarioNames))]" /></template>
          <template #filter="{ filterModel }">
            <UInput v-model="filterModel.value" type="text" placeholder="Search by scenario" />
          </template>
        </Column>
              <Column header="Contacts" style="width: 6rem">
                <template #body="{ data }">{{ data.members.length }}</template>
              </Column>
              <Column v-if="!readOnly" header="" style="width: 3rem">
                <template #body="{ data }">
                  <UButton
                    icon="i-lucide-more-vertical"
                    color="neutral"
                    variant="ghost"
                    square
                    aria-label="Contact options"
                    @click.stop="openGroupContextMenu($event, data)"
                  />
                </template>
              </Column>

              <template #expansion="{ data: group }">
                <DataTable
                  :value="group.members"
                  data-key="id"
                  edit-mode="cell"
                  :row-class="() => 'hover:bg-elevated'"
                  @row-contextmenu="(event: { originalEvent: Event; data: Contact }) => openMemberContextMenu(event.originalEvent, event.data)"
                  @cell-edit-complete="onMemberNameEditComplete"
                >
                  <Column header="Name" field="name">
                    <template #body="{ data }">
                      <UInput
                        v-if="editingNames"
                        :model-value="data.name"
                        :placeholder="contactFallbackName(data)"
                        class="w-full"
                        @update:model-value="(value: string) => onMemberNameInput(data, value)"
                        @blur="onMemberNameBlur(data)"
                        @keyup.enter="($event.target as HTMLElement)?.blur()"
                      />
                      <template v-else>{{ data.name || contactFallbackName(data) }}</template>
                    </template>
                    <template v-if="!editingNames && !readOnly" #editor="{ data, field }">
                      <UInput v-model="data[field]" autofocus class="w-full" @keyup.enter="($event.target as HTMLElement)?.blur()" />
                    </template>
                  </Column>
                  <Column header="Donor">
                    <template #body="{ data }">
                      <span class="flex items-center gap-1.5">
                        <UIcon v-if="sideIcon(data, 'donor_surface')" :name="sideIcon(data, 'donor_surface')!" class="shrink-0" />
                        {{ sideIndividualLabel(data, 'donor_surface') ?? sideDisplay(data, 'donor_surface').label }}
                        <UBadge v-if="sideIndividual(data, 'donor_surface')?.sex?.name" color="neutral" variant="outline">
                          {{ sideIndividual(data, 'donor_surface')!.sex!.name }}
                        </UBadge>
                        <UBadge v-if="sideIndividual(data, 'donor_surface')?.age != null" color="neutral" variant="outline">
                          {{ sideIndividual(data, 'donor_surface')!.age }}y
                        </UBadge>
                      </span>
                    </template>
                  </Column>
                  <Column header="Recipient">
                    <template #body="{ data }">
                      <span class="flex items-center gap-1.5">
                        <UIcon v-if="sideIcon(data, 'recipient_surface')" :name="sideIcon(data, 'recipient_surface')!" class="shrink-0" />
                        {{ sideIndividualLabel(data, 'recipient_surface') ?? sideDisplay(data, 'recipient_surface').label }}
                        <UBadge v-if="sideIndividual(data, 'recipient_surface')?.sex?.name" color="neutral" variant="outline">
                          {{ sideIndividual(data, 'recipient_surface')!.sex!.name }}
                        </UBadge>
                        <UBadge v-if="sideIndividual(data, 'recipient_surface')?.age != null" color="neutral" variant="outline">
                          {{ sideIndividual(data, 'recipient_surface')!.age }}y
                        </UBadge>
                      </span>
                    </template>
                  </Column>
                  <Column v-if="!readOnly" header="" style="width: 3rem">
                    <template #body="{ data }">
                      <UButton
                        icon="i-lucide-more-vertical"
                        color="neutral"
                        variant="ghost"
                        square
                        aria-label="Contact options"
                        @click.stop="openMemberContextMenu($event, data)"
                      />
                    </template>
                  </Column>
                </DataTable>
              </template>
            </DataTable>
          </div>

          <ContactInstanceDialog
            v-if="!readOnly"
            v-model:visible="dialogVisible"
            :study-id="studyId"
            :contact-templates="visibleTemplates"
            :contacts="visibleContacts"
            :contact-label="contactLabel"
            :scenarios="studyScenarios"
            :scenario-id="selectedScenarioId"
            @saved="onContactSaved"
          />

          <UModal
            v-model:open="chainDialogVisible"
            title="Set previous contact"
            :ui="{ content: 'max-w-lg', footer: 'justify-end' }"
          >
            <template #body>
              <UFormField label="Follows contact" hint="The earlier contact in the chain">
                <USelect v-model="chainValue" :items="chainItems" class="w-full" />
              </UFormField>
            </template>
            <template #footer>
              <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="chainDialogVisible = false" />
              <UButton label="Save" icon="i-lucide-save" :loading="chaining" @click="saveChain" />
            </template>
          </UModal>

          <UModal
            v-model:open="renameDialogVisible"
            title="Rename contact"
            :ui="{ content: 'max-w-sm', footer: 'justify-end' }"
          >
            <template #body>
              <UFormField label="Name" hint="Optional - helps tell otherwise identical contacts apart">
                <UInput v-model="renameValue" class="w-full" @keyup.enter="saveRename" />
              </UFormField>
            </template>
            <template #footer>
              <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="renameDialogVisible = false" />
              <UButton label="Save" icon="i-lucide-save" :loading="renaming" @click="saveRename" />
            </template>
          </UModal>
        </div>
      </template>

      <template #samples>
        <SamplesPanel
          :study-id="studyId"
          :contacts="visibleContacts"
          :contact-templates="visibleTemplates"
          :surface-scenarios="surfaceScenarios"
          :scenarios="studyScenarios"
          :export-name="exportName"
          @update:samples="scopedSamples = $event"
        />
      </template>

      <template #results>
        <ResultsTab :samples="scopedSamples" :study-id="studyId" :surface-scenarios="surfaceScenarios" :contacts="contacts" :export-name="exportName" />
      </template>
    </UTabs>
  </div>
</template>
