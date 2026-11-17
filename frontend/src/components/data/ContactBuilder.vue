<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useToast } from '@nuxt/ui/composables'
import { useIndividualOptions } from '@/components/scenarios/individualOptions'
import { plannedTemplateSequences } from './contactChain'
import { templateName, surfaceIcon, surfaceDetail } from './contactTemplateLabel'
import {
  CONTACT_SIDES,
  autoLinkDrafts,
  canPlaceIndividual,
  contactRef,
  draftRef,
  linkDraft,
  predecessorOptions,
  pruneDraftLinks,
  draftIndividual,
  draftProblem,
  freeSideFor,
  individualSides,
  isItemSide,
  newContactDraft,
  saveContactDrafts,
  setDraftIndividual,
  sideTemplate,
  templateProblem,
} from './contactBuilder'
import type { ContactDraft, ContactSide } from './contactBuilder'
import type { ContactChainInfo } from './ContactChainNode.vue'
import type { LinkOp } from './ContactChains.vue'
import type { Contact, ContactTemplate, Individual, Scenario } from '@/api/types'

const props = defineProps<{
  studyId: string
  scenarios: Scenario[]
  // The scenario selected on the page, or null for "All data".
  scenarioId: string | null
  contactTemplates: ContactTemplate[]
  contacts: Contact[]
  info: (contact: Contact) => ContactChainInfo
  // Individuals are reloaded whenever the board is shown again, so ones
  // added on the Individuals tab in the meantime show up.
  active: boolean
  // Whether the last change to recorded links can be undone.
  canUndo?: boolean
}>()

// `change` and `undo` edit links between recorded contacts, which are
// saved right away (with undo), like on the chain board.
const emit = defineEmits<{ saved: [contacts: Contact[]]; change: [ops: LinkOp[]]; undo: [] }>()

const toast = useToast()

const { individuals, describeIndividual, load: loadIndividuals } = useIndividualOptions(props.studyId)

watch(
  () => props.active,
  (active, wasActive) => {
    if (active && wasActive === false) loadIndividuals()
  },
)

// -- Templates and the scenarios they belong to --

const sequences = computed(() => plannedTemplateSequences(props.contactTemplates))

const templateById = computed(() => new Map(props.contactTemplates.map((t) => [t.id, t])))

const templateScenarioIds = computed(() => {
  const map = new Map<string, Set<string>>()
  for (const scenario of props.scenarios) {
    for (const template of scenario.contact_templates) {
      const ids = map.get(template.id) ?? new Set<string>()
      ids.add(scenario.id)
      map.set(template.id, ids)
    }
  }
  return map
})

// An individual can only be used in a contact of a scenario it is assigned to.
function individualFits(template: ContactTemplate, individual: Individual): boolean {
  const scenarioIds = templateScenarioIds.value.get(template.id)
  if (!scenarioIds?.size) return true
  return (individual.scenario_ids ?? []).some((id) => scenarioIds.has(id))
}

function individualsFor(template: ContactTemplate): Individual[] {
  return individuals.value.filter((individual) => individualFits(template, individual))
}

// -- Individuals palette --

const search = ref('')
const selectedIds = ref<string[]>([])

const scopedIndividuals = computed(() =>
  props.scenarioId
    ? individuals.value.filter((individual) => individual.scenario_ids?.includes(props.scenarioId!))
    : individuals.value,
)

const individualById = computed(() => new Map(individuals.value.map((i) => [i.id, i])))

const paletteIndividuals = computed(() => {
  const needle = search.value.trim().toLowerCase()
  if (!needle) return scopedIndividuals.value
  return scopedIndividuals.value.filter((individual) =>
    describeIndividual(individual).toLowerCase().includes(needle),
  )
})

function toggleSelected(id: string) {
  selectedIds.value = selectedIds.value.includes(id)
    ? selectedIds.value.filter((selected) => selected !== id)
    : [...selectedIds.value, id]
}

function selectAllVisible() {
  selectedIds.value = [...new Set([...selectedIds.value, ...paletteIndividuals.value.map((i) => i.id)])]
}

function individualLabel(id: string | null): string {
  const individual = id ? individualById.value.get(id) : null
  return individual ? describeIndividual(individual) : 'Unknown individual'
}

// -- Drafts --

const drafts = ref<ContactDraft[]>([])

const draftsByTemplate = computed(() => {
  const map = new Map<string, ContactDraft[]>()
  for (const draft of drafts.value) {
    const list = map.get(draft.templateId) ?? []
    list.push(draft)
    map.set(draft.templateId, list)
  }
  return map
})

// How many drafts each individual takes part in, shown on the palette.
const draftUse = computed(() => {
  const counts = new Map<string, number>()
  for (const draft of drafts.value) {
    for (const id of new Set([draft.donorIndividualId, draft.recipientIndividualId])) {
      if (id) counts.set(id, (counts.get(id) ?? 0) + 1)
    }
  }
  return counts
})

const recordedByTemplate = computed(() => {
  const map = new Map<string, Contact[]>()
  for (const contact of props.contacts) {
    if (!contact.contact_template_id) continue
    const list = map.get(contact.contact_template_id) ?? []
    list.push(contact)
    map.set(contact.contact_template_id, list)
  }
  return map
})

const draftByRef = computed(() => new Map(drafts.value.map((d) => [draftRef(d), d])))

function problemOf(draft: ContactDraft, seen = new Set<string>()): string | null {
  const template = templateById.value.get(draft.templateId)
  if (!template) return 'This contact template is no longer available.'
  const own = draftProblem(draft, template)
  if (own) return own
  // A draft is only saved together with the draft it follows.
  const previous = draft.previousRef ? draftByRef.value.get(draft.previousRef) : undefined
  if (previous && !seen.has(previous.key)) {
    seen.add(draft.key)
    if (problemOf(previous, seen)) return 'Follows a new contact that is not complete yet.'
  }
  return null
}

// -- Chaining while creating --

const contactById = computed(() => new Map(props.contacts.map((c) => [c.id, c])))

function hasPreviousStep(template: ContactTemplate): boolean {
  const previousId = template.previous_contact_template_id
  return !!previousId && templateById.value.has(previousId)
}

function draftSideLabel(draft: ContactDraft, side: ContactSide): string {
  const template = templateById.value.get(draft.templateId)
  if (!template || !sideTemplate(template, side)) return '—'
  if (isItemSide(template, side)) return itemName(template, side)
  const id = draftIndividual(draft, side)
  return id ? individualLabel(id) : '?'
}

function draftLabel(draft: ContactDraft): string {
  return `${draftSideLabel(draft, 'donor')} → ${draftSideLabel(draft, 'recipient')}`
}

function recordedLabel(contact: Contact): string {
  const info = props.info(contact)
  return `${info.title} (${info.donor.label} → ${info.recipient.label})`
}

function refLabel(ref: string): string {
  const draft = draftByRef.value.get(ref)
  if (draft) return `New: ${draftLabel(draft)}`
  const contact = ref.startsWith('contact:') ? contactById.value.get(ref.slice('contact:'.length)) : undefined
  return contact ? recordedLabel(contact) : 'Unknown contact'
}

const NO_PREVIOUS = '__none__'

function previousItems(draft: ContactDraft) {
  const options = predecessorOptions(draft, drafts.value, props.contacts, templateById.value)
  const groups: { label: string; value?: string; type?: 'label' }[][] = [
    [{ label: 'Nothing (starts a chain)', value: NO_PREVIOUS }],
  ]
  if (options.drafts.length) {
    groups.push([
      { type: 'label', label: 'New contacts' },
      ...options.drafts.map((d) => ({ label: draftLabel(d), value: draftRef(d) })),
    ])
  }
  if (options.contacts.length) {
    groups.push([
      { type: 'label', label: 'Recorded contacts' },
      ...options.contacts.map((c) => ({ label: recordedLabel(c), value: contactRef(c) })),
    ])
  }
  // Keep the current choice selectable even though it is "taken" by this draft.
  if (draft.previousRef && !groups.flat().some((item) => item.value === draft.previousRef)) {
    groups.push([{ label: refLabel(draft.previousRef), value: draft.previousRef }])
  }
  return groups
}

function setPrevious(draft: ContactDraft, value: string | undefined) {
  linkDraft(drafts.value, draft, !value || value === NO_PREVIOUS ? null : value)
}

function followerOf(ref: string): ContactDraft | undefined {
  return drafts.value.find((d) => d.previousRef === ref)
}

// Proposes links by shared individual for every draft not linked by hand.
// Automatic chaining can be switched off; the choice is remembered in this
// browser.
const AUTO_CHAIN_KEY = 'transact.contactBuilder.autoChain'

function readAutoChain(): boolean {
  try {
    return localStorage.getItem(AUTO_CHAIN_KEY) !== 'false'
  } catch {
    return true
  }
}

const autoChain = ref(readAutoChain())

watch(autoChain, (enabled) => {
  try {
    localStorage.setItem(AUTO_CHAIN_KEY, String(enabled))
  } catch {
    // Not remembered, but still applies for now.
  }
  if (enabled) {
    autoLink()
    return
  }
  // Switching off removes the links that were made automatically; links
  // set by hand (Follows, Next step, drag and drop) stay.
  for (const draft of drafts.value) {
    if (!draft.linkTouched) draft.previousRef = null
  }
})

function autoLink() {
  if (autoChain.value) autoLinkDrafts(drafts.value, props.contacts, templateById.value)
}
watch(drafts, autoLink, { deep: true })
watch(() => props.contacts, autoLink)

const readyDrafts = computed(() => drafts.value.filter((draft) => !problemOf(draft)))
const incompleteCount = computed(() => drafts.value.length - readyDrafts.value.length)

// Adds the individuals to a template: each one first fills a free slot of a
// draft that is still missing someone (so dropping A, B, C, D on a template
// with individuals on both sides pairs them up as A-B and C-D), otherwise
// it starts a new contact.
function addIndividuals(template: ContactTemplate, ids: string[]) {
  if (!individualSides(template).length) return
  const skipped: string[] = []
  const added: ContactDraft[] = []
  for (const id of ids) {
    const individual = individualById.value.get(id)
    if (!individual || !individualFits(template, individual)) {
      skipped.push(individualLabel(id))
      continue
    }
    const candidates = [...added, ...(draftsByTemplate.value.get(template.id) ?? [])]
    const open = candidates.find((draft) => freeSideFor(draft, template, id))
    if (open) {
      setDraftIndividual(open, freeSideFor(open, template, id)!, id)
      continue
    }
    const draft = newContactDraft(template.id)
    setDraftIndividual(draft, individualSides(template)[0]!, id)
    added.push(draft)
  }
  addOnTop(added)
  if (skipped.length) {
    toast.add({
      title: `${skipped.length} individual${skipped.length === 1 ? '' : 's'} not added`,
      description: `Not assigned to a scenario of "${templateName(template)}": ${skipped.join(', ')}`,
      color: 'warning',
      icon: 'i-lucide-user-x',
    })
  }
}

function addSelected(template: ContactTemplate) {
  addIndividuals(template, selectedIds.value)
}

// New drafts go on top of their column, in the order they were added.
function addOnTop(added: ContactDraft[]) {
  if (added.length) drafts.value = [...added, ...drafts.value]
}

function addEmptyDraft(template: ContactTemplate) {
  addOnTop([newContactDraft(template.id)])
}

// -- Continue a chain: add the next step's contact, already linked --

const nextTemplateById = computed(() => {
  const map = new Map<string, ContactTemplate>()
  for (const sequence of sequences.value) {
    sequence.forEach((template, index) => {
      const next = sequence[index + 1]
      if (next) map.set(template.id, next)
    })
  }
  return map
})

const followedRecordedIds = computed(
  () => new Set(props.contacts.map((c) => c.previous_contact_id).filter((id): id is string => !!id)),
)

function nextTemplateFor(templateId: string | null | undefined): ContactTemplate | undefined {
  return templateId ? nextTemplateById.value.get(templateId) : undefined
}

// A contact can be continued when its step has a next step and nothing
// follows it yet (each contact can only be followed by one other contact).
function canContinue(ref: string, templateId: string | null | undefined): boolean {
  if (!nextTemplateFor(templateId) || followerOf(ref)) return false
  return !ref.startsWith('contact:') || !followedRecordedIds.value.has(ref.slice('contact:'.length))
}

const flashKey = ref<string | null>(null)

async function continueChain(ref: string, templateId: string | null | undefined) {
  const next = nextTemplateFor(templateId)
  if (!next || !canContinue(ref, templateId)) return
  const draft = newContactDraft(next.id)
  draft.previousRef = ref
  draft.linkTouched = true
  addOnTop([draft])
  flashKey.value = draft.key
  await nextTick()
  document
    .getElementById(`contact-draft-${draft.key}`)
    ?.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: 'smooth' })
  setTimeout(() => {
    if (flashKey.value === draft.key) flashKey.value = null
  }, 1500)
}

// -- Chain status of recorded contacts --

const recordedFollowerById = computed(() => {
  const map = new Map<string, Contact>()
  for (const contact of props.contacts) {
    if (contact.previous_contact_id) map.set(contact.previous_contact_id, contact)
  }
  return map
})

function recordedFollower(contact: Contact): Contact | undefined {
  return recordedFollowerById.value.get(contact.id)
}

// "chained": linked to a recorded contact before or after it; "pending": a
// new contact on the board will follow it once saved; "none": not chained.
function recordedChainState(contact: Contact): 'chained' | 'pending' | 'none' {
  if (contact.previous_contact_id || recordedFollower(contact)) return 'chained'
  return followerOf(contactRef(contact)) ? 'pending' : 'none'
}

function recordedGroups(templateId: string) {
  const all = recordedByTemplate.value.get(templateId) ?? []
  return {
    unchained: all.filter((c) => recordedChainState(c) !== 'chained'),
    chained: all.filter((c) => recordedChainState(c) === 'chained'),
  }
}

function removeDraft(draft: ContactDraft) {
  drafts.value = drafts.value.filter((candidate) => candidate.key !== draft.key)
  pruneDraftLinks(drafts.value)
}

function clearTemplateDrafts(template: ContactTemplate) {
  drafts.value = drafts.value.filter((draft) => draft.templateId !== template.id)
  pruneDraftLinks(drafts.value)
}

function setSlot(draft: ContactDraft, side: ContactSide, id: string | null) {
  const template = templateById.value.get(draft.templateId)
  if (!template) return
  if (id && !canPlaceIndividual(draft, template, side, id)) {
    toast.add({
      title: 'Already in this contact',
      description: 'An individual can only take part once per contact. Use a different individual for the other side.',
      color: 'warning',
      icon: 'i-lucide-user-x',
    })
    return
  }
  setDraftIndividual(draft, side, id)
}

// Options for an individual slot: everyone of the template's scenarios
// except whoever is already on the other side of this contact.
function slotItems(draft: ContactDraft, side: ContactSide) {
  const template = templateById.value.get(draft.templateId)
  if (!template) return []
  return individualsFor(template)
    .filter((individual) => canPlaceIndividual(draft, template, side, individual.id))
    .map((individual) => ({ label: describeIndividual(individual), value: individual.id }))
}

// -- Board rows: every chain is one row, its contacts side by side --

interface BoardNode {
  ref: string
  templateId: string
  draft?: ContactDraft
  contact?: Contact
}

interface BoardRow {
  key: string
  cells: (BoardNode | null)[]
  size: number
  hasDraft: boolean
  rank: number
}

function previousRefOf(node: BoardNode): string | null {
  if (node.draft) return node.draft.previousRef
  return node.contact?.previous_contact_id ? `contact:${node.contact.previous_contact_id}` : null
}

function rowsFor(sequence: ContactTemplate[]): BoardRow[] {
  const position = new Map(sequence.map((template, index) => [template.id, index]))
  const nodes: BoardNode[] = [
    ...drafts.value
      .filter((draft) => position.has(draft.templateId))
      .map((draft) => ({ ref: draftRef(draft), templateId: draft.templateId, draft })),
    ...props.contacts
      .filter((contact) => position.has(contact.contact_template_id ?? ''))
      .map((contact) => ({ ref: contactRef(contact), templateId: contact.contact_template_id!, contact })),
  ]
  const byRef = new Map(nodes.map((node) => [node.ref, node]))
  const nextOf = new Map<string, BoardNode>()
  for (const node of nodes) {
    const previous = previousRefOf(node)
    if (previous && byRef.has(previous) && !nextOf.has(previous)) nextOf.set(previous, node)
  }
  const draftIndex = new Map(drafts.value.map((draft, index) => [draftRef(draft), index]))
  const placed = new Set<string>()
  const rows: BoardRow[] = []
  const startRow = (root: BoardNode) => {
    const cells: (BoardNode | null)[] = sequence.map(() => null)
    let size = 0
    let rank = Number.POSITIVE_INFINITY
    for (let node: BoardNode | undefined = root; node && !placed.has(node.ref); node = nextOf.get(node.ref)) {
      const index = position.get(node.templateId)!
      // A chain that runs into an occupied step continues in a row of its own.
      if (cells[index]) break
      placed.add(node.ref)
      cells[index] = node
      size += 1
      if (node.draft) rank = Math.min(rank, draftIndex.get(node.ref)!)
    }
    rows.push({ key: root.ref, cells, size, hasDraft: rank !== Number.POSITIVE_INFINITY, rank })
  }
  for (const node of nodes) {
    const previous = previousRefOf(node)
    const isRoot = !previous || nextOf.get(previous) !== node
    if (isRoot && !placed.has(node.ref)) startRow(node)
  }
  for (const node of nodes) if (!placed.has(node.ref)) startRow(node)
  // New contacts on top (newest first), then recorded chains, then
  // recorded contacts that are not chained.
  return rows.sort((a, b) => {
    if (a.hasDraft || b.hasDraft) return a.rank - b.rank
    return (b.size > 1 ? 1 : 0) - (a.size > 1 ? 1 : 0)
  })
}

type RowFilter = 'all' | 'new' | 'unchained' | 'chained'

const rowFilter = ref<RowFilter>('all')

function rowMatches(row: BoardRow, filter: RowFilter): boolean {
  if (filter === 'new') return row.hasDraft
  if (filter === 'unchained') return row.size === 1
  if (filter === 'chained') return row.size > 1
  return true
}

const sequenceRows = computed(() => new Map(sequences.value.map((sequence) => [sequence[0]!.id, rowsFor(sequence)])))

function visibleRows(sequence: ContactTemplate[]): BoardRow[] {
  return (sequenceRows.value.get(sequence[0]!.id) ?? []).filter((row) => rowMatches(row, rowFilter.value))
}

const rowFilterItems = computed(() => {
  const all = [...sequenceRows.value.values()].flat()
  const count = (filter: RowFilter) => all.filter((row) => rowMatches(row, filter)).length
  return [
    { label: `All (${count('all')})`, value: 'all' },
    { label: `New (${count('new')})`, value: 'new' },
    { label: `Not chained (${count('unchained')})`, value: 'unchained', icon: 'i-lucide-unlink' },
    { label: `Chained (${count('chained')})`, value: 'chained', icon: 'i-lucide-link' },
  ]
})

// Whether the cell at `index` is linked to the one after it.
function linkedToNext(row: BoardRow, index: number): boolean {
  const current = row.cells[index]
  const next = row.cells[index + 1]
  return !!current && !!next && previousRefOf(next) === current.ref
}

// Removes the link of `node` to the contact before it. Links between
// recorded contacts are saved right away (with undo); a new contact's link
// only changes the draft.
function unlinkPrevious(node: BoardNode) {
  if (node.draft) linkDraft(drafts.value, node.draft, null)
  else if (node.contact) emit('change', [{ contactId: node.contact.id, previousId: null }])
}

// The "+ Next step" cell goes right after the last contact of a row.
function nextStepIndex(row: BoardRow): number | null {
  let last = -1
  row.cells.forEach((cell, index) => {
    if (cell) last = index
  })
  const node = row.cells[last]
  if (!node || last + 1 >= row.cells.length) return null
  return canContinue(node.ref, node.templateId) ? last + 1 : null
}

// Each sequence's board scrolls on its own; long chains (5-10 steps) get a
// step navigation that scrolls the board to that step.
const boardRefs = new Map<string, HTMLElement>()

function setBoardRef(key: string, el: unknown) {
  if (el instanceof HTMLElement) boardRefs.set(key, el)
  else boardRefs.delete(key)
}

function scrollToStep(sequence: ContactTemplate[], index: number) {
  const board = boardRefs.get(sequence[0]!.id)
  const header = board?.querySelector<HTMLElement>(`[data-step="${index}"]`)
  if (board && header) board.scrollTo({ left: header.offsetLeft - 4, behavior: 'smooth' })
}

// -- Items --

function itemName(template: ContactTemplate, side: ContactSide): string {
  const item = sideTemplate(template, side)?.item
  const name = item?.item_subcategory?.name ?? item?.item_category?.name ?? 'Item'
  const part = sideTemplate(template, side)?.item_parts_category?.name
  return part ? `${name} (${part})` : name
}

// -- Drag and drop --

const dragged = ref<string[]>([])
const hoverTarget = ref<string | null>(null)

function onDragStart(event: DragEvent, id: string) {
  dragged.value = selectedIds.value.includes(id) ? [...selectedIds.value] : [id]
  event.dataTransfer?.setData('text/plain', dragged.value.join(','))
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'copy'
}

function onDragEnd() {
  dragged.value = []
  hoverTarget.value = null
}

function canDropOnTemplate(template: ContactTemplate): boolean {
  if (!individualSides(template).length || templateProblem(template)) return false
  return dragged.value.some((id) => {
    const individual = individualById.value.get(id)
    return !!individual && individualFits(template, individual)
  })
}

function canDropOnSlot(draft: ContactDraft, side: ContactSide): boolean {
  const template = templateById.value.get(draft.templateId)
  const id = dragged.value[0]
  const individual = id ? individualById.value.get(id) : null
  return (
    dragged.value.length === 1 &&
    !!template &&
    !!individual &&
    individualFits(template, individual) &&
    canPlaceIndividual(draft, template, side, individual.id)
  )
}

function onDragOver(event: DragEvent, target: string, allowed: boolean) {
  if (!allowed) return
  event.preventDefault()
  hoverTarget.value = target
}

function dropOnTemplate(template: ContactTemplate) {
  if (canDropOnTemplate(template)) addIndividuals(template, dragged.value)
  onDragEnd()
}

function dropOnSlot(draft: ContactDraft, side: ContactSide) {
  if (canDropOnSlot(draft, side)) setSlot(draft, side, dragged.value[0]!)
  onDragEnd()
}

// Dragging a new contact onto a contact of the neighbouring step chains them,
// in either direction - like on the chain board.
const draggedDraft = ref<ContactDraft | null>(null)

function onDraftDragStart(event: DragEvent, draft: ContactDraft) {
  draggedDraft.value = draft
  event.dataTransfer?.setData('text/plain', draft.key)
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'link'
}

function onDraftDragEnd() {
  draggedDraft.value = null
  hoverTarget.value = null
}

// Which draft gets linked to which contact when the dragged draft is
// dropped on `target`, or null when they are not in neighbouring steps.
function linkForDrop(target: ContactDraft | Contact): { draft: ContactDraft; previousRef: string } | null {
  const source = draggedDraft.value
  if (!source) return null
  const targetIsDraft = 'key' in target
  if (targetIsDraft && target.key === source.key) return null
  const targetTemplateId = targetIsDraft ? target.templateId : target.contact_template_id
  const targetRef = targetIsDraft ? draftRef(target) : contactRef(target)
  const sourceTemplate = templateById.value.get(source.templateId)
  // The dragged draft follows the target.
  if (sourceTemplate?.previous_contact_template_id === targetTemplateId) {
    const free = predecessorOptions(source, drafts.value, props.contacts, templateById.value)
    const allowed = targetIsDraft
      ? free.drafts.some((d) => d.key === target.key)
      : free.contacts.some((c) => c.id === target.id)
    return allowed || source.previousRef === targetRef ? { draft: source, previousRef: targetRef } : null
  }
  // The target (a draft) follows the dragged draft.
  if (targetIsDraft && templateById.value.get(target.templateId)?.previous_contact_template_id === source.templateId) {
    return { draft: target, previousRef: draftRef(source) }
  }
  return null
}

function canLinkDrop(target: ContactDraft | Contact): boolean {
  return !!linkForDrop(target)
}

function dropDraftOn(target: ContactDraft | Contact) {
  const link = linkForDrop(target)
  if (link) linkDraft(drafts.value, link.draft, link.previousRef)
  onDraftDragEnd()
}

// -- Saving --

const saving = ref(false)

async function save() {
  if (!readyDrafts.value.length) return
  saving.value = true
  const result = await saveContactDrafts(readyDrafts.value, props.contactTemplates)
  saving.value = false
  const savedKeys = new Set(result.savedKeys)
  // Drafts left on the board keep their link to a draft that is now saved.
  const savedRefs = new Map(result.savedKeys.map((key, index) => [`draft:${key}`, `contact:${result.saved[index]!.id}`]))
  drafts.value = drafts.value.filter((draft) => !savedKeys.has(draft.key))
  for (const draft of drafts.value) {
    if (draft.previousRef && savedRefs.has(draft.previousRef)) draft.previousRef = savedRefs.get(draft.previousRef)!
  }
  if (result.saved.length) emit('saved', result.saved)
  if (result.error) {
    toast.add({
      title: 'Could not save all contacts',
      description: `${result.saved.length} saved. The remaining drafts are still on the board, so you can try again.`,
      color: 'error',
      icon: 'i-lucide-circle-alert',
    })
  }
}

function sideIcon(template: ContactTemplate, side: ContactSide) {
  return surfaceIcon(sideTemplate(template, side))
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <ol class="text-xs text-muted max-w-3xl flex flex-col gap-1 list-none">
        <li class="flex gap-2">
          <UBadge label="1" color="neutral" variant="soft" size="sm" class="shrink-0" />
          <span>
            <span class="text-default font-medium">Create:</span> drag individuals onto a step (or select them
            and click "Add selected"). One contact per individual; on steps with individuals on both sides
            they are paired up as donor and recipient.
          </span>
        </li>
        <li class="flex gap-2">
          <UBadge label="2" color="neutral" variant="soft" size="sm" class="shrink-0" />
          <span>
            <span class="text-default font-medium">Chain:</span> every row is one chain, its contacts side by
            side with <UIcon name="i-lucide-arrow-right" class="align-middle text-primary" /> between them. Click
            <span class="text-default">+ Next step</span> at the end of a row to add the following contact, or
            choose under "Follows". With "Chain automatically" on, contacts sharing an individual with one in the
            previous step are chained for you. Click an arrow to remove that link.
          </span>
        </li>
        <li class="flex gap-2">
          <UBadge label="3" color="neutral" variant="soft" size="sm" class="shrink-0" />
          <span><span class="text-default font-medium">Save</span> - contacts and their links are saved together.</span>
        </li>
      </ol>
      <div class="flex flex-wrap items-center gap-2">
        <USwitch
          v-model="autoChain"
          label="Chain automatically"
          size="sm"
          title="Link new contacts to a contact of the previous step that shares an individual"
        />
        <UButton
          label="Undo"
          icon="i-lucide-undo-2"
          color="neutral"
          variant="outline"
          size="sm"
          title="Undo the last change to links between recorded contacts"
          :disabled="!canUndo"
          @click="emit('undo')"
        />
        <UButton
          label="Discard drafts"
          icon="i-lucide-trash-2"
          color="neutral"
          variant="ghost"
          size="sm"
          :disabled="!drafts.length || saving"
          @click="drafts = []"
        />
        <UButton
          :label="readyDrafts.length === 1 ? 'Save 1 contact' : `Save ${readyDrafts.length} contacts`"
          icon="i-lucide-save"
          size="sm"
          :loading="saving"
          :disabled="!readyDrafts.length"
          @click="save"
        />
      </div>
    </div>

    <UAlert
      v-if="incompleteCount"
      color="warning"
      variant="subtle"
      icon="i-lucide-circle-alert"
      :description="`${incompleteCount} draft${incompleteCount === 1 ? ' is' : 's are'} not complete yet and will not be saved.`"
    />

    <div class="grid gap-4 lg:grid-cols-[16rem_minmax(0,1fr)]">
      <!-- Individuals palette -->
      <div class="rounded-md border border-default flex flex-col lg:sticky lg:top-4 lg:self-start lg:max-h-[calc(100vh-2rem)]">
        <div class="px-3 py-2 border-b border-default flex items-center justify-between gap-2">
          <span class="font-medium text-sm">Individuals</span>
          <UBadge color="neutral" variant="subtle" :label="String(scopedIndividuals.length)" />
        </div>
        <div class="p-2 flex flex-col gap-2 border-b border-default">
          <UInput v-model="search" icon="i-lucide-search" placeholder="Search individuals" size="sm" class="w-full" />
          <div class="flex items-center justify-between gap-2 text-xs">
            <span class="text-muted">{{ selectedIds.length }} selected</span>
            <span class="flex gap-1">
              <UButton label="All" variant="link" size="xs" :disabled="!paletteIndividuals.length" @click="selectAllVisible" />
              <UButton label="None" variant="link" size="xs" :disabled="!selectedIds.length" @click="selectedIds = []" />
            </span>
          </div>
        </div>
        <div class="flex flex-col gap-1 p-2 overflow-y-auto max-h-96 lg:max-h-none">
          <p v-if="!paletteIndividuals.length" class="text-xs text-muted p-1">
            {{ scopedIndividuals.length ? 'No individuals match your search.' : 'Add individuals on the Individuals tab first.' }}
          </p>
          <div
            v-for="individual in paletteIndividuals"
            :key="individual.id"
            draggable="true"
            :class="[
              'rounded-md border px-2 py-1.5 text-xs flex items-center gap-2 cursor-grab select-none transition-colors',
              selectedIds.includes(individual.id) ? 'border-primary bg-primary/10' : 'border-default hover:bg-elevated',
              dragged.includes(individual.id) ? 'opacity-50' : '',
            ]"
            @dragstart="onDragStart($event, individual.id)"
            @dragend="onDragEnd"
            @click="toggleSelected(individual.id)"
          >
            <UCheckbox
              :model-value="selectedIds.includes(individual.id)"
              size="xs"
              :aria-label="`Select ${describeIndividual(individual)}`"
              @click.stop
              @update:model-value="toggleSelected(individual.id)"
            />
            <UIcon name="i-lucide-user" class="shrink-0 text-muted" />
            <span class="truncate flex-1">{{ describeIndividual(individual) }}</span>
            <UBadge
              v-if="draftUse.get(individual.id)"
              color="primary"
              variant="subtle"
              size="sm"
              :label="String(draftUse.get(individual.id))"
              :title="`In ${draftUse.get(individual.id)} draft contact(s)`"
            />
            <UIcon name="i-lucide-grip-vertical" class="shrink-0 text-dimmed" />
          </div>
        </div>
      </div>

      <!-- Contact steps in planned order; every row is one chain. Only this
           area scrolls sideways, the individuals list stays in place. -->
      <div class="flex flex-col gap-4 min-w-0">
        <UAlert
          v-if="!contactTemplates.length"
          color="info"
          variant="outline"
          description="Plan a scenario with at least one contact template before entering actual data."
        />
        <div v-if="contactTemplates.length" class="flex flex-wrap items-center justify-between gap-2">
          <UTabs v-model="rowFilter" :items="rowFilterItems" :content="false" variant="pill" size="xs" class="w-fit" />
          <span class="text-xs text-muted">Scroll sideways (or Shift + mouse wheel) to see all steps.</span>
        </div>

        <div v-for="sequence in sequences" :key="sequence[0]!.id" class="rounded-md border border-default min-w-0">
          <!-- Step navigation for long chains -->
          <div v-if="sequence.length > 3" class="flex gap-1 overflow-x-auto border-b border-default p-1.5">
            <UButton
              v-for="(template, index) in sequence"
              :key="template.id"
              :label="`${index + 1}. ${templateName(template)}`"
              color="neutral"
              variant="ghost"
              size="xs"
              class="shrink-0 max-w-48"
              :ui="{ label: 'truncate' }"
              @click="scrollToStep(sequence, index)"
            />
          </div>

          <div :ref="(el) => setBoardRef(sequence[0]!.id, el)" class="relative overflow-auto max-h-[75vh]">
            <!-- Step headers -->
            <div class="flex w-max sticky top-0 z-10 bg-default border-b border-default p-1">
              <template v-for="(template, index) in sequence" :key="template.id">
                <div :data-step="index" class="w-64 shrink-0 flex flex-col gap-1.5 p-1">
                  <div class="flex items-center justify-between gap-2">
                    <span class="font-medium text-sm truncate" :title="templateName(template)">
                      <span v-if="sequence.length > 1" class="text-muted">{{ index + 1 }}.</span>
                      {{ templateName(template) }}
                    </span>
                    <span class="flex shrink-0 gap-1">
                      <UBadge
                        color="success"
                        variant="subtle"
                        size="sm"
                        icon="i-lucide-link"
                        :label="String(recordedGroups(template.id).chained.length)"
                        title="Recorded contacts that are chained"
                      />
                      <UBadge
                        color="neutral"
                        variant="subtle"
                        size="sm"
                        icon="i-lucide-unlink"
                        :label="String(recordedGroups(template.id).unchained.length)"
                        title="Recorded contacts that are not chained yet"
                      />
                    </span>
                  </div>
                  <span class="flex items-center gap-1 text-xs text-muted min-w-0">
                    <UIcon v-if="sideIcon(template, 'donor')" :name="sideIcon(template, 'donor')!" class="shrink-0" />
                    <span class="truncate">{{ surfaceDetail(template.donor_surface_template) }}</span>
                    <UIcon name="i-lucide-arrow-right" class="shrink-0" />
                    <UIcon v-if="sideIcon(template, 'recipient')" :name="sideIcon(template, 'recipient')!" class="shrink-0" />
                    <span class="truncate">{{ surfaceDetail(template.recipient_surface_template) }}</span>
                  </span>

                  <UAlert
                    v-if="templateProblem(template)"
                    color="error"
                    variant="subtle"
                    :description="templateProblem(template)!"
                  />
                  <template v-else>
                    <p
                      v-if="CONTACT_SIDES.some((s) => isItemSide(template, s))"
                      class="flex items-start gap-1 text-xs text-muted"
                      :title="`Each contact gets its own ${CONTACT_SIDES.filter((s) => isItemSide(template, s)).map((s) => itemName(template, s)).join(' and ')}: the same kind of item, never the identical one.`"
                    >
                      <UIcon name="i-lucide-package" class="shrink-0 mt-0.5" />
                      <span class="truncate">
                        Own {{ CONTACT_SIDES.filter((s) => isItemSide(template, s)).map((s) => itemName(template, s)).join(' and ') }} per contact
                      </span>
                    </p>
                    <div
                      v-if="individualSides(template).length"
                      :class="[
                        'rounded-md border border-dashed px-2 py-1.5 text-xs flex items-center justify-between gap-1 transition-colors',
                        hoverTarget === `template:${template.id}`
                          ? 'border-primary bg-primary/10'
                          : dragged.length && canDropOnTemplate(template)
                            ? 'border-primary'
                            : 'border-default text-muted',
                        dragged.length && !canDropOnTemplate(template) ? 'opacity-50' : '',
                      ]"
                      @dragover="onDragOver($event, `template:${template.id}`, canDropOnTemplate(template))"
                      @dragleave="hoverTarget = null"
                      @drop.prevent="dropOnTemplate(template)"
                    >
                      <span class="flex items-center gap-1 truncate">
                        <UIcon name="i-lucide-user-plus" class="shrink-0" />
                        Drop individuals
                      </span>
                      <span class="flex shrink-0 gap-0.5">
                        <UButton
                          :label="`Add ${selectedIds.length}`"
                          icon="i-lucide-plus"
                          variant="outline"
                          size="xs"
                          :disabled="!selectedIds.length"
                          title="Add one contact per selected individual"
                          @click="addSelected(template)"
                        />
                        <UButton
                          icon="i-lucide-plus"
                          variant="ghost"
                          size="xs"
                          square
                          aria-label="Add an empty contact"
                          title="Add an empty contact"
                          @click="addEmptyDraft(template)"
                        />
                      </span>
                    </div>
                    <UButton
                      v-else
                      label="Add contact"
                      icon="i-lucide-plus"
                      variant="outline"
                      size="xs"
                      block
                      @click="addEmptyDraft(template)"
                    />
                    <div v-if="draftsByTemplate.get(template.id)?.length" class="flex items-center justify-between text-xs">
                      <span class="text-muted">{{ draftsByTemplate.get(template.id)!.length }} new</span>
                      <UButton label="Clear" variant="link" size="xs" color="neutral" @click="clearTemplateDrafts(template)" />
                    </div>
                  </template>
                </div>
                <div v-if="index < sequence.length - 1" class="w-8 shrink-0 flex justify-center pt-2">
                  <UIcon name="i-lucide-arrow-right" class="text-dimmed" />
                </div>
              </template>
            </div>

            <!-- Rows: one chain each -->
            <div class="flex flex-col gap-1.5 p-1 w-max">
              <p v-if="!visibleRows(sequence).length" class="text-xs text-muted p-2">
                {{ rowFilter === 'all' ? 'No contacts yet. Drop individuals on a step above.' : 'No contacts match this filter.' }}
              </p>
              <div
                v-for="row in visibleRows(sequence)"
                :key="row.key"
                :class="[
                  'flex w-max rounded-md p-1',
                  row.size > 1 ? 'bg-elevated/60 ring-1 ring-default' : '',
                ]"
              >
                <template v-for="(cell, index) in row.cells" :key="index">
                  <div class="w-64 shrink-0 min-w-0">
                    <!-- New contact -->
                    <div
                      v-if="cell?.draft"
                      :id="`contact-draft-${cell.draft.key}`"
                      :class="[
                        'rounded-md border p-2 text-xs flex flex-col gap-1 bg-default transition-colors',
                        hoverTarget === cell.ref
                          ? 'border-primary ring-2 ring-primary bg-primary/10'
                          : draggedDraft && canLinkDrop(cell.draft)
                            ? 'border-primary border-dashed'
                            : flashKey === cell.draft.key
                              ? 'border-primary ring-2 ring-primary/50'
                              : problemOf(cell.draft)
                                ? 'border-warning/60'
                                : 'border-primary/60',
                        draggedDraft?.key === cell.draft.key ? 'opacity-40' : '',
                        draggedDraft && draggedDraft.key !== cell.draft.key && !canLinkDrop(cell.draft) ? 'opacity-50' : '',
                      ]"
                      @dragover="draggedDraft && onDragOver($event, cell.ref, canLinkDrop(cell.draft))"
                      @dragleave="hoverTarget = null"
                      @drop.prevent="draggedDraft && dropDraftOn(cell.draft)"
                    >
                      <div class="flex items-center justify-between gap-1 -mt-0.5">
                        <span
                          draggable="true"
                          class="flex items-center gap-1 text-dimmed cursor-grab select-none"
                          title="Drag onto a contact of the previous or next step to chain them"
                          @dragstart="onDraftDragStart($event, cell.draft)"
                          @dragend="onDraftDragEnd"
                        >
                          <UIcon name="i-lucide-grip-horizontal" />
                          <span>New</span>
                        </span>
                        <UBadge v-if="row.size === 1" label="Not chained" icon="i-lucide-unlink" color="neutral" variant="subtle" size="sm" class="ml-auto" />
                        <UButton
                          icon="i-lucide-x"
                          color="neutral"
                          variant="ghost"
                          size="xs"
                          square
                          aria-label="Remove new contact"
                          @click="removeDraft(cell.draft)"
                        />
                      </div>
                      <div
                        v-if="hasPreviousStep(templateById.get(cell.templateId)!) && !(index > 0 && linkedToNext(row, index - 1))"
                        class="flex items-center gap-1 min-w-0"
                      >
                        <span class="shrink-0 text-muted">Follows</span>
                        <USelectMenu
                          :model-value="cell.draft.previousRef ?? NO_PREVIOUS"
                          :items="previousItems(cell.draft)"
                          value-key="value"
                          :search-input="{ placeholder: 'Search contacts' }"
                          size="xs"
                          class="flex-1 min-w-0"
                          :color="cell.draft.previousRef ? 'primary' : 'neutral'"
                          :ui="{ base: 'w-full min-w-0', content: 'w-72 max-w-[calc(100vw-2rem)]' }"
                          aria-label="Contact this one follows"
                          @update:model-value="(value: string | undefined) => setPrevious(cell.draft!, value)"
                        />
                      </div>
                      <template v-for="(side, sideIndex) in CONTACT_SIDES" :key="side">
                        <UIcon v-if="sideIndex > 0" name="i-lucide-arrow-down" class="text-dimmed self-center" />
                        <div
                          v-if="individualSides(templateById.get(cell.templateId)!).includes(side)"
                          :class="[
                            'rounded flex items-center gap-1 min-w-0 transition-colors',
                            hoverTarget === `${cell.draft.key}:${side}` ? 'ring-2 ring-primary bg-primary/10' : '',
                            dragged.length === 1 && canDropOnSlot(cell.draft, side) ? 'ring-1 ring-primary' : '',
                          ]"
                          @dragover="onDragOver($event, `${cell.draft.key}:${side}`, canDropOnSlot(cell.draft, side))"
                          @dragleave="hoverTarget = null"
                          @drop.prevent="dropOnSlot(cell.draft, side)"
                        >
                          <USelectMenu
                            :model-value="draftIndividual(cell.draft, side) ?? undefined"
                            :items="slotItems(cell.draft, side)"
                            value-key="value"
                            :placeholder="`Pick or drop ${side}`"
                            :search-input="{ placeholder: 'Search individuals' }"
                            icon="i-lucide-user"
                            size="xs"
                            class="flex-1 min-w-0"
                            :color="draftIndividual(cell.draft, side) ? 'primary' : 'warning'"
                            :ui="{ base: 'w-full min-w-0', content: 'w-72 max-w-[calc(100vw-2rem)]' }"
                            @update:model-value="(value: string | undefined) => setSlot(cell.draft!, side, value ?? null)"
                          />
                        </div>
                        <div
                          v-else-if="sideTemplate(templateById.get(cell.templateId)!, side)"
                          class="flex items-center gap-1 px-1 py-0.5 text-muted min-w-0"
                        >
                          <UIcon name="i-lucide-package" class="shrink-0" />
                          <span class="truncate">{{ itemName(templateById.get(cell.templateId)!, side) }}</span>
                        </div>
                        <div v-else class="px-1 py-0.5 text-dimmed">No {{ side }}</div>
                      </template>
                      <span v-if="problemOf(cell.draft)" class="text-warning truncate" :title="problemOf(cell.draft)!">
                        {{ problemOf(cell.draft) }}
                      </span>
                      <span v-else class="text-primary flex items-center gap-1">
                        <UIcon name="i-lucide-check" /> Ready
                      </span>
                    </div>

                    <!-- Recorded contact -->
                    <div
                      v-else-if="cell?.contact"
                      :class="[
                        'rounded-md border px-2 py-1.5 text-xs flex flex-col gap-0.5 bg-default transition-colors',
                        hoverTarget === cell.ref
                          ? 'border-primary ring-2 ring-primary bg-primary/10'
                          : draggedDraft && canLinkDrop(cell.contact)
                            ? 'border-primary border-dashed'
                            : row.size > 1
                              ? 'border-success/50'
                              : 'border-default border-dashed',
                      ]"
                      @dragover="draggedDraft && onDragOver($event, cell.ref, canLinkDrop(cell.contact))"
                      @dragleave="hoverTarget = null"
                      @drop.prevent="draggedDraft && dropDraftOn(cell.contact)"
                    >
                      <span class="flex items-center justify-between gap-1">
                        <span class="font-medium truncate" :title="info(cell.contact).title">{{ info(cell.contact).title }}</span>
                        <UBadge v-if="row.size === 1" label="Not chained" icon="i-lucide-unlink" color="neutral" variant="subtle" size="sm" class="shrink-0" />
                        <UBadge v-else label="Recorded" color="neutral" variant="outline" size="sm" class="shrink-0" />
                      </span>
                      <span class="flex items-center gap-1 text-muted min-w-0">
                        <span class="truncate">{{ info(cell.contact).donor.label }}</span>
                        <UIcon name="i-lucide-arrow-right" class="shrink-0" />
                        <span class="truncate">{{ info(cell.contact).recipient.label }}</span>
                      </span>
                    </div>

                    <!-- Continue the chain in this step -->
                    <button
                      v-else-if="nextStepIndex(row) === index"
                      type="button"
                      class="w-full h-full min-h-14 rounded-md border border-dashed border-primary/50 text-xs text-primary flex items-center justify-center gap-1 hover:bg-primary/10 transition-colors"
                      :title="`Add the next contact of this chain in '${templateName(sequence[index]!)}'`"
                      @click="continueChain(row.cells[index - 1]!.ref, row.cells[index - 1]!.templateId)"
                    >
                      <UIcon name="i-lucide-plus" /> Next step
                    </button>
                  </div>

                  <!-- Link between neighbouring contacts; click to remove it -->
                  <div v-if="index < row.cells.length - 1" class="w-8 shrink-0 flex items-center justify-center">
                    <UButton
                      v-if="linkedToNext(row, index)"
                      color="primary"
                      variant="ghost"
                      size="xs"
                      square
                      class="group"
                      :aria-label="`Remove link to step ${index + 2}`"
                      title="Linked - click to remove this link"
                      @click="unlinkPrevious(row.cells[index + 1]!)"
                    >
                      <UIcon name="i-lucide-arrow-right" class="size-4 group-hover:hidden" />
                      <UIcon name="i-lucide-unlink" class="size-4 hidden group-hover:block text-error" />
                    </UButton>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
