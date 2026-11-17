import { createContact } from '@/api/contacts'
import { createSurface } from '@/api/surfaces'
import { contactIndividualIds } from './contactChain'
import type { Contact, ContactTemplate, SurfaceTemplate } from '@/api/types'

export type ContactSide = 'donor' | 'recipient'

export const CONTACT_SIDES: ContactSide[] = ['donor', 'recipient']

// A contact that is being put together on the board and not saved yet. Only
// the individual slots are filled in by hand: an item slot's item is fixed
// by the template.
export interface ContactDraft {
  key: string
  templateId: string
  donorIndividualId: string | null
  recipientIndividualId: string | null
  // The contact this one follows in its chain: another draft (`draft:<key>`)
  // or an already recorded contact (`contact:<id>`).
  previousRef: string | null
  // Set once the link was chosen or removed by hand, so automatic linking
  // leaves it alone from then on.
  linkTouched: boolean
}

let draftCounter = 0

export function newContactDraft(templateId: string): ContactDraft {
  draftCounter += 1
  return {
    key: `draft-${draftCounter}`,
    templateId,
    donorIndividualId: null,
    recipientIndividualId: null,
    previousRef: null,
    linkTouched: false,
  }
}

export const draftRef = (draft: ContactDraft) => `draft:${draft.key}`
export const contactRef = (contact: Contact) => `contact:${contact.id}`

export function draftIndividualIds(draft: ContactDraft): string[] {
  return [draft.donorIndividualId, draft.recipientIndividualId].filter((id): id is string => !!id)
}

// Links a draft to the contact it follows. A contact can be followed by only
// one other contact, so any other draft following the same one lets go (and
// may be linked automatically again elsewhere).
export function linkDraft(drafts: ContactDraft[], draft: ContactDraft, previousRef: string | null) {
  if (previousRef) {
    for (const other of drafts) {
      if (other !== draft && other.previousRef === previousRef) {
        other.previousRef = null
        other.linkTouched = false
      }
    }
  }
  draft.previousRef = previousRef
  draft.linkTouched = true
}

// Lets go of links to drafts that no longer exist.
export function pruneDraftLinks(drafts: ContactDraft[]) {
  const refs = new Set(drafts.map(draftRef))
  for (const draft of drafts) {
    if (draft.previousRef?.startsWith('draft:') && !refs.has(draft.previousRef)) draft.previousRef = null
  }
}

// Contacts a draft may follow: drafts and recorded contacts of the template
// its own template follows, that nothing else follows yet.
export function predecessorOptions(
  draft: ContactDraft,
  drafts: ContactDraft[],
  recorded: Contact[],
  templateById: Map<string, ContactTemplate>,
): { drafts: ContactDraft[]; contacts: Contact[] } {
  const previousTemplateId = templateById.get(draft.templateId)?.previous_contact_template_id
  if (!previousTemplateId || !templateById.has(previousTemplateId)) return { drafts: [], contacts: [] }
  const taken = new Set(
    drafts.filter((d) => d !== draft).map((d) => d.previousRef).filter((ref): ref is string => !!ref),
  )
  const followedRecorded = new Set(recorded.map((c) => c.previous_contact_id).filter(Boolean))
  return {
    drafts: drafts.filter((d) => d.templateId === previousTemplateId && !taken.has(draftRef(d))),
    contacts: recorded.filter(
      (c) =>
        c.contact_template_id === previousTemplateId &&
        !followedRecorded.has(c.id) &&
        !taken.has(contactRef(c)),
    ),
  }
}

// Links drafts that are not linked yet (and were not unlinked by hand) to a
// free predecessor sharing an individual with them - another draft first,
// otherwise a recorded contact. Individuals may recur along a chain.
export function autoLinkDrafts(
  drafts: ContactDraft[],
  recorded: Contact[],
  templateById: Map<string, ContactTemplate>,
) {
  for (const draft of drafts) {
    if (draft.previousRef || draft.linkTouched) continue
    const own = new Set(draftIndividualIds(draft))
    if (!own.size) continue
    const options = predecessorOptions(draft, drafts, recorded, templateById)
    const fromDraft = options.drafts.find((d) => draftIndividualIds(d).some((id) => own.has(id)))
    if (fromDraft) {
      draft.previousRef = draftRef(fromDraft)
      continue
    }
    const fromContact = options.contacts.find((c) => contactIndividualIds(c).some((id) => own.has(id)))
    if (fromContact) draft.previousRef = contactRef(fromContact)
  }
}

export function sideTemplate(template: ContactTemplate, side: ContactSide): SurfaceTemplate | null {
  return (side === 'donor' ? template.donor_surface_template : template.recipient_surface_template) ?? null
}

export function isIndividualSide(template: ContactTemplate, side: ContactSide): boolean {
  const surface = sideTemplate(template, side)
  return !!surface && !surface.item_id
}

export function isItemSide(template: ContactTemplate, side: ContactSide): boolean {
  return !!sideTemplate(template, side)?.item_id
}

export function individualSides(template: ContactTemplate): ContactSide[] {
  return CONTACT_SIDES.filter((side) => isIndividualSide(template, side))
}

export function draftIndividual(draft: ContactDraft, side: ContactSide): string | null {
  return side === 'donor' ? draft.donorIndividualId : draft.recipientIndividualId
}

export function setDraftIndividual(draft: ContactDraft, side: ContactSide, individualId: string | null) {
  if (side === 'donor') draft.donorIndividualId = individualId
  else draft.recipientIndividualId = individualId
}

// An individual or an item can only take part once in a single contact - it
// cannot be both donor and recipient. (Across the contacts of a chain they
// may occur any number of times.)
export function canPlaceIndividual(
  draft: ContactDraft,
  template: ContactTemplate,
  side: ContactSide,
  individualId: string,
): boolean {
  if (!isIndividualSide(template, side)) return false
  const otherSide: ContactSide = side === 'donor' ? 'recipient' : 'donor'
  return draftIndividual(draft, otherSide) !== individualId
}

// The first free individual slot of the draft that may take this individual.
export function freeSideFor(
  draft: ContactDraft,
  template: ContactTemplate,
  individualId: string,
): ContactSide | null {
  return (
    individualSides(template).find(
      (side) => !draftIndividual(draft, side) && canPlaceIndividual(draft, template, side, individualId),
    ) ?? null
  )
}

export function templateProblem(template: ContactTemplate): string | null {
  if (!template.donor_surface_template && !template.recipient_surface_template) {
    return 'This contact template has no donor or recipient.'
  }
  const donorItem = template.donor_surface_template?.item_id
  if (donorItem && donorItem === template.recipient_surface_template?.item_id) {
    return 'Donor and recipient are the same item. An item can only be used once per contact.'
  }
  return null
}

// Why a draft cannot be saved yet, or null when it is complete.
export function draftProblem(draft: ContactDraft, template: ContactTemplate): string | null {
  const fromTemplate = templateProblem(template)
  if (fromTemplate) return fromTemplate
  for (const side of individualSides(template)) {
    if (!draftIndividual(draft, side)) return `Pick the ${side}.`
  }
  if (draft.donorIndividualId && draft.donorIndividualId === draft.recipientIndividualId) {
    return 'An individual can only take part once per contact.'
  }
  return null
}

export interface SaveDraftsResult {
  saved: Contact[]
  savedKeys: string[]
  error: unknown
}

// Creates the surfaces and contacts for the given drafts. Every contact gets
// fresh surfaces of its own - in particular for items: contacts with the
// same tool use the same kind of item, never the identical surface ("das
// gleiche, aber nicht dasselbe"). Stops at the first failure and reports
// what was saved up to that point, so the board can keep only the drafts
// that still need saving.
export async function saveContactDrafts(
  drafts: ContactDraft[],
  templates: ContactTemplate[],
): Promise<SaveDraftsResult> {
  const templateById = new Map(templates.map((t) => [t.id, t]))
  const result: SaveDraftsResult = { saved: [], savedKeys: [], error: null }

  async function surfaceFor(draft: ContactDraft, template: ContactTemplate, side: ContactSide) {
    const surfaceTemplate = sideTemplate(template, side)
    if (!surfaceTemplate) return null
    return createSurface({
      surface_template_id: surfaceTemplate.id,
      individual_id: surfaceTemplate.item_id ? null : draftIndividual(draft, side),
    })
  }

  // Predecessors are saved before the drafts that follow them, so the link
  // can point at the contact just created.
  const byRef = new Map(drafts.map((d) => [draftRef(d), d]))
  const depth = (draft: ContactDraft, seen = new Set<string>()): number => {
    const previous = draft.previousRef ? byRef.get(draft.previousRef) : undefined
    if (!previous || seen.has(previous.key)) return 0
    seen.add(previous.key)
    return depth(previous, seen) + 1
  }
  const ordered = [...drafts].sort((a, b) => depth(a) - depth(b))
  const createdByRef = new Map<string, string>()

  function previousContactId(draft: ContactDraft): string | null | undefined {
    const ref = draft.previousRef
    if (!ref) return null
    if (ref.startsWith('contact:')) return ref.slice('contact:'.length)
    // undefined: the draft it follows was not saved, so neither is this one.
    return createdByRef.get(ref)
  }

  try {
    for (const draft of ordered) {
      const template = templateById.get(draft.templateId)
      if (!template || draftProblem(draft, template)) continue
      const previousId = previousContactId(draft)
      if (previousId === undefined) continue
      const donor = await surfaceFor(draft, template, 'donor')
      const recipient = await surfaceFor(draft, template, 'recipient')
      result.saved.push(
        await createContact({
          contact_template_id: template.id,
          donor_surface_id: donor?.id ?? null,
          recipient_surface_id: recipient?.id ?? null,
          previous_contact_id: previousId,
        }),
      )
      createdByRef.set(draftRef(draft), result.saved.at(-1)!.id)
      result.savedKeys.push(draft.key)
    }
  } catch (error) {
    result.error = error
  }
  return result
}
