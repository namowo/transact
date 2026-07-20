import {
  createConditionDuringContact,
  createContact,
  updateConditionDuringContact,
  updateContact,
} from '@/api/contacts'
import { emptySurfaceDraft, saveSurfaceDraft, surfaceDraftFromSurface } from './surfaceDraft'
import type { SurfaceDraft } from './surfaceDraft'
import type { Contact } from '@/api/types'

export interface ContactDraft {
  id: number | null
  donorSurface: SurfaceDraft
  donorSurfaceId: number | null
  recipientSurface: SurfaceDraft
  recipientSurfaceId: number | null
  // Seconds.
  duration: number | null
  pressure: number | null
  frictionApplied: number | null
  contactArea: number | null
  descriptionOfContact: string | null
  activityCategoryId: number | null
  conditionDuringContactId: number | null
  temperature: number | null
  humidity: number | null
  uvIrradiation: number | null
  indoors: boolean
}

export function emptyContactDraft(): ContactDraft {
  return {
    id: null,
    donorSurface: emptySurfaceDraft(),
    donorSurfaceId: null,
    recipientSurface: emptySurfaceDraft(),
    recipientSurfaceId: null,
    duration: null,
    pressure: null,
    frictionApplied: null,
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

export function contactDraftFromContact(contact: Contact): ContactDraft {
  return {
    id: contact.id,
    donorSurface: surfaceDraftFromSurface(contact.donor_surface),
    donorSurfaceId: contact.donor_surface_id ?? null,
    recipientSurface: surfaceDraftFromSurface(contact.recipient_surface),
    recipientSurfaceId: contact.recipient_surface_id ?? null,
    duration: contact.duration ?? null,
    pressure: contact.pressure ?? null,
    frictionApplied: contact.friction_applied ?? null,
    contactArea: contact.contact_area ?? null,
    descriptionOfContact: contact.description_of_contact ?? null,
    activityCategoryId: contact.activity_category_id ?? null,
    conditionDuringContactId: contact.condition_during_contact_id ?? null,
    temperature: contact.condition_during_contact?.temperature ?? null,
    humidity: contact.condition_during_contact?.humidity ?? null,
    uvIrradiation: contact.condition_during_contact?.uv_irradiation ?? null,
    indoors: !!contact.condition_during_contact?.indoors,
  }
}

function hasConditionData(draft: ContactDraft): boolean {
  return (
    draft.temperature != null ||
    draft.humidity != null ||
    draft.uvIrradiation != null ||
    draft.indoors
  )
}

export async function saveContactDraft(draft: ContactDraft, scenarioId: number): Promise<void> {
  const donorSurfaceId = await saveSurfaceDraft(draft.donorSurface, draft.donorSurfaceId)
  const recipientSurfaceId = await saveSurfaceDraft(
    draft.recipientSurface,
    draft.recipientSurfaceId,
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
    scenario_id: scenarioId,
    donor_surface_id: donorSurfaceId,
    recipient_surface_id: recipientSurfaceId,
    duration: draft.duration,
    pressure: draft.pressure,
    friction_applied: draft.frictionApplied,
    contact_area: draft.contactArea,
    description_of_contact: draft.descriptionOfContact || null,
    activity_category_id: draft.activityCategoryId,
    condition_during_contact_id: conditionDuringContactId,
  }

  if (draft.id) {
    await updateContact(draft.id, payload)
  } else {
    await createContact(payload)
  }
}
