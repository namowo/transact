import { createContactTemplate, updateContactTemplate } from '@/api/contactTemplates'
import { createConditionDuringContact, updateConditionDuringContact } from '@/api/contacts'
import {
  emptySurfaceTemplateDraft,
  saveSurfaceTemplateDraft,
  surfaceTemplateDraftFromSurfaceTemplate,
} from './surfaceTemplateDraft'
import type { SurfaceTemplateDraft } from './surfaceTemplateDraft'
import type { ContactTemplate } from '@/api/types'

export interface ContactTemplateDraft {
  id: string | null
  // Stable client-side identity, so a draft can be referenced as another
  // draft's predecessor before either has been saved. Equals the saved id
  // when the draft was loaded from an existing template.
  uid: string
  // uid of the draft this one directly follows in the chain.
  followsUid: string | null
  name: string | null
  donorSurfaceTemplate: SurfaceTemplateDraft
  donorSurfaceTemplateId: string | null
  recipientSurfaceTemplate: SurfaceTemplateDraft
  recipientSurfaceTemplateId: string | null
  // Seconds.
  duration: number | null
  pressureEstimateId: string | null
  frictionAppliedEstimateId: string | null
  contactArea: number | null
  descriptionOfContact: string | null
  activityCategoryId: string | null
  conditionDuringContactId: string | null
  temperature: number | null
  humidity: number | null
  uvIrradiation: number | null
  indoors: boolean
}

export function emptyContactTemplateDraft(): ContactTemplateDraft {
  return {
    id: null,
    uid: crypto.randomUUID(),
    followsUid: null,
    name: null,
    donorSurfaceTemplate: emptySurfaceTemplateDraft(),
    donorSurfaceTemplateId: null,
    recipientSurfaceTemplate: emptySurfaceTemplateDraft(),
    recipientSurfaceTemplateId: null,
    duration: null,
    pressureEstimateId: null,
    frictionAppliedEstimateId: null,
    contactArea: null,
    descriptionOfContact: null,
    activityCategoryId: null,
    conditionDuringContactId: null,
    temperature: null,
    humidity: null,
    uvIrradiation: null,
    indoors: false,
  }
}

export function contactTemplateDraftFromContactTemplate(
  template: ContactTemplate,
): ContactTemplateDraft {
  return {
    id: template.id,
    uid: template.id,
    followsUid: template.previous_contact_template_id ?? null,
    name: template.name ?? null,
    donorSurfaceTemplate: surfaceTemplateDraftFromSurfaceTemplate(template.donor_surface_template),
    donorSurfaceTemplateId: template.donor_surface_template_id ?? null,
    recipientSurfaceTemplate: surfaceTemplateDraftFromSurfaceTemplate(
      template.recipient_surface_template,
    ),
    recipientSurfaceTemplateId: template.recipient_surface_template_id ?? null,
    duration: template.duration ?? null,
    pressureEstimateId: template.pressure_estimate_id ?? null,
    frictionAppliedEstimateId: template.friction_applied_estimate_id ?? null,
    contactArea: template.contact_area ?? null,
    descriptionOfContact: template.description_of_contact ?? null,
    activityCategoryId: template.activity_category_id ?? null,
    conditionDuringContactId: template.condition_during_contact_id ?? null,
    temperature: template.condition_during_contact?.temperature ?? null,
    humidity: template.condition_during_contact?.humidity ?? null,
    uvIrradiation: template.condition_during_contact?.uv_irradiation ?? null,
    indoors: !!template.condition_during_contact?.indoors,
  }
}

// Used when duplicating a scenario from another study: keeps the field
// values but drops every id (including the nested surface templates and
// condition-during-contact), so saving creates independent copies instead of
// updating the originals. Chain links are dropped too; use
// cloneContactTemplateDraftsForDuplication to keep them between copies.
export function cloneContactTemplateDraftForDuplication(
  draft: ContactTemplateDraft,
): ContactTemplateDraft {
  return {
    ...draft,
    id: null,
    uid: crypto.randomUUID(),
    followsUid: null,
    donorSurfaceTemplateId: null,
    recipientSurfaceTemplateId: null,
    conditionDuringContactId: null,
  }
}

// Clones a whole set of drafts, re-pointing each chain link at the copy of
// its predecessor so the chain survives duplication intact.
export function cloneContactTemplateDraftsForDuplication(
  drafts: ContactTemplateDraft[],
): ContactTemplateDraft[] {
  const copies = drafts.map(cloneContactTemplateDraftForDuplication)
  const copyUidByOriginal = new Map(drafts.map((d, i) => [d.uid, copies[i]!.uid]))
  copies.forEach((copy, i) => {
    const follows = drafts[i]!.followsUid
    copy.followsUid = follows ? (copyUidByOriginal.get(follows) ?? null) : null
  })
  return copies
}

// Walks the chain backwards from a draft; true when it loops back on itself.
export function contactTemplateChainHasCycle(drafts: ContactTemplateDraft[]): boolean {
  const followsByUid = new Map(drafts.map((d) => [d.uid, d.followsUid]))
  for (const draft of drafts) {
    const seen = new Set<string>([draft.uid])
    let next = draft.followsUid
    while (next && followsByUid.has(next)) {
      if (seen.has(next)) return true
      seen.add(next)
      next = followsByUid.get(next) ?? null
    }
  }
  return false
}

export type ChainSlot =
  | { kind: 'after'; uid: string }
  | { kind: 'start'; uid: string } // before the given draft, which must be a chain head
  | { kind: 'detach' }

// Moves a draft within the chains, keeping them linear: the draft is lifted
// out of its current chain (its neighbours close the gap) and put into the
// slot. Mutates the drafts' followsUid.
export function moveContactTemplateInChain(
  drafts: ContactTemplateDraft[],
  uid: string,
  slot: ChainSlot,
) {
  const moved = drafts.find((d) => d.uid === uid)
  if (!moved || (slot.kind !== 'detach' && slot.uid === uid)) return
  const successorOf = (u: string) => drafts.find((d) => d.followsUid === u)

  const successor = successorOf(uid)
  if (successor) successor.followsUid = moved.followsUid
  moved.followsUid = null

  if (slot.kind === 'after') {
    const next = successorOf(slot.uid)
    if (next) next.followsUid = uid
    moved.followsUid = slot.uid
  } else if (slot.kind === 'start') {
    const head = drafts.find((d) => d.uid === slot.uid)
    if (head) head.followsUid = uid
  }
}

// Clears chain links pointing at a draft that is being removed.
export function unlinkContactTemplateDraft(drafts: ContactTemplateDraft[], uid: string) {
  for (const draft of drafts) if (draft.followsUid === uid) draft.followsUid = null
}

export function isBlankContactTemplateDraft(draft: ContactTemplateDraft): boolean {
  return draft.donorSurfaceTemplate.kind === null && draft.recipientSurfaceTemplate.kind === null
}

function hasConditionData(draft: ContactTemplateDraft): boolean {
  return (
    draft.temperature != null ||
    draft.humidity != null ||
    draft.uvIrradiation != null ||
    draft.indoors
  )
}

// Persists the ContactTemplate (and its donor/recipient SurfaceTemplates),
// linking it to the given scenario. Returns the saved ContactTemplate's id.
// The chain link is not written here, since the predecessor may not be saved
// yet; see saveContactTemplateChain.
export async function saveContactTemplateDraft(
  draft: ContactTemplateDraft,
  scenarioId: string,
): Promise<string> {
  const donorSurfaceTemplateId = await saveSurfaceTemplateDraft(
    draft.donorSurfaceTemplate,
    draft.donorSurfaceTemplateId,
  )
  const recipientSurfaceTemplateId = await saveSurfaceTemplateDraft(
    draft.recipientSurfaceTemplate,
    draft.recipientSurfaceTemplateId,
  )

  let conditionDuringContactId = draft.conditionDuringContactId
  if (hasConditionData(draft)) {
    const payload = {
      temperature: draft.temperature,
      humidity: draft.humidity,
      uv_irradiation: draft.uvIrradiation,
      indoors: draft.indoors,
    }
    conditionDuringContactId = conditionDuringContactId
      ? (await updateConditionDuringContact(conditionDuringContactId, payload)).id
      : (await createConditionDuringContact(payload)).id
  }

  const payload = {
    name: draft.name || null,
    donor_surface_template_id: donorSurfaceTemplateId,
    recipient_surface_template_id: recipientSurfaceTemplateId,
    duration: draft.duration,
    pressure_estimate_id: draft.pressureEstimateId,
    friction_applied_estimate_id: draft.frictionAppliedEstimateId,
    contact_area: draft.contactArea,
    description_of_contact: draft.descriptionOfContact || null,
    activity_category_id: draft.activityCategoryId,
    condition_during_contact_id: conditionDuringContactId,
    scenario_ids: [scenarioId],
  }

  const template = draft.id
    ? await updateContactTemplate(draft.id, payload)
    : await createContactTemplate(payload)
  return template.id
}

// Writes the chain links once every draft has an id. Predecessors that no
// longer exist among the drafts (e.g. removed from the form) clear the link.
export async function saveContactTemplateChain(
  drafts: ContactTemplateDraft[],
  savedIds: string[],
): Promise<void> {
  const idByUid = new Map(drafts.map((d, i) => [d.uid, savedIds[i]!]))
  await Promise.all(
    drafts.map((draft, i) =>
      updateContactTemplate(savedIds[i]!, {
        previous_contact_template_id: draft.followsUid ? (idByUid.get(draft.followsUid) ?? null) : null,
      }),
    ),
  )
}
