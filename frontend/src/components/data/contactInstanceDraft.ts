import { createContact } from '@/api/contacts'
import {
  emptySurfaceInstanceDraft,
  saveSurfaceInstanceDraft,
} from './surfaceInstanceDraft'
import type { SurfaceInstanceDraft } from './surfaceInstanceDraft'
import type { Contact, ContactTemplate } from '@/api/types'

export interface ContactInstanceDraft {
  contactTemplateId: number | null
  donorSurface: SurfaceInstanceDraft
  recipientSurface: SurfaceInstanceDraft
}

export function emptyContactInstanceDraft(): ContactInstanceDraft {
  return {
    contactTemplateId: null,
    donorSurface: emptySurfaceInstanceDraft(),
    recipientSurface: emptySurfaceInstanceDraft(),
  }
}

// Creates the actual donor/recipient Surface rows (instantiating the
// template's SurfaceTemplates) and the actual Contact that ties them
// together under the chosen ContactTemplate.
export async function saveContactInstanceDraft(
  draft: ContactInstanceDraft,
  contactTemplate: ContactTemplate,
): Promise<Contact> {
  const donorSurface = await saveSurfaceInstanceDraft(
    draft.donorSurface,
    contactTemplate.donor_surface_template ?? null,
  )
  const recipientSurface = await saveSurfaceInstanceDraft(
    draft.recipientSurface,
    contactTemplate.recipient_surface_template ?? null,
  )

  return createContact({
    contact_template_id: contactTemplate.id,
    donor_surface_id: donorSurface?.id ?? null,
    recipient_surface_id: recipientSurface?.id ?? null,
  })
}
