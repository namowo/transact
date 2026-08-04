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
  id: number | null
  donorSurfaceTemplate: SurfaceTemplateDraft
  donorSurfaceTemplateId: number | null
  recipientSurfaceTemplate: SurfaceTemplateDraft
  recipientSurfaceTemplateId: number | null
  // Seconds.
  duration: number | null
  pressureEstimateId: number | null
  frictionAppliedEstimateId: number | null
  contactArea: number | null
  descriptionOfContact: string | null
  activityCategoryId: number | null
  conditionDuringContactId: number | null
  temperature: number | null
  humidity: number | null
  uvIrradiation: number | null
  indoors: boolean
}

export function emptyContactTemplateDraft(): ContactTemplateDraft {
  return {
    id: null,
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
export async function saveContactTemplateDraft(
  draft: ContactTemplateDraft,
  scenarioId: number,
): Promise<number> {
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
