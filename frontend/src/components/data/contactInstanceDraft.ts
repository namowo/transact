import { createContact } from '@/api/contacts'
import {
  emptySurfaceInstanceDraft,
  saveSurfaceInstanceDraft,
  createRequiredSurfaceInstance,
} from './surfaceInstanceDraft'
import type { SurfaceInstanceDraft } from './surfaceInstanceDraft'
import type { Contact, ContactTemplate, Surface, SurfaceTemplate } from '@/api/types'

export interface ContactInstanceDraft {
  contactTemplateId: string | null
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

// Creates one SurfaceInstanceDraft's Surface for a template slot (or reuses
// an existing one per the draft). An item slot always produces a Surface
// once a template is defined - the item is implied by the template, not by
// anything the user fills in - whereas an individual slot only produces one
// once an individual has actually been picked, since skipping it there
// leaves an intentionally-unused slot alone.
function saveSlotSurfaceInstanceDraft(
  draft: SurfaceInstanceDraft,
  template: SurfaceTemplate | null,
  existingSurfaces: Surface[],
): Promise<Surface | null> {
  if (template?.item_id) return createRequiredSurfaceInstance(draft, template, existingSurfaces)
  return saveSurfaceInstanceDraft(draft, template, existingSurfaces)
}

// Creates the actual donor/recipient Surface rows (instantiating the
// template's SurfaceTemplates, or reusing an existing Surface the draft
// points to) and the actual Contact that ties them together under the
// chosen ContactTemplate.
export async function saveContactInstanceDraft(
  draft: ContactInstanceDraft,
  contactTemplate: ContactTemplate,
  existingSurfaces: Surface[] = [],
): Promise<Contact> {
  const donorSurface = await saveSlotSurfaceInstanceDraft(
    draft.donorSurface,
    contactTemplate.donor_surface_template ?? null,
    existingSurfaces,
  )
  const recipientSurface = await saveSlotSurfaceInstanceDraft(
    draft.recipientSurface,
    contactTemplate.recipient_surface_template ?? null,
    existingSurfaces,
  )

  return createContact({
    contact_template_id: contactTemplate.id,
    donor_surface_id: donorSurface?.id ?? null,
    recipient_surface_id: recipientSurface?.id ?? null,
  })
}

// Creates one actual Contact per individual, all sharing the same item-side
// surface instance (the item surface is fixed per batch, only the
// individual side varies). Used when exactly one of the template's two
// surfaces is an individual slot - batching doesn't make sense when both
// sides are individuals, since each pairing has to be picked by hand.
export async function saveContactInstanceBatch(
  draft: ContactInstanceDraft,
  contactTemplate: ContactTemplate,
  individualSide: 'donor' | 'recipient',
  individualIds: string[],
  existingSurfaces: Surface[] = [],
): Promise<Contact[]> {
  const itemSide = individualSide === 'donor' ? 'recipient' : 'donor'
  const itemSurfaceTemplate =
    (itemSide === 'donor'
      ? contactTemplate.donor_surface_template
      : contactTemplate.recipient_surface_template) ?? null
  const itemSurfaceDraft = itemSide === 'donor' ? draft.donorSurface : draft.recipientSurface

  const itemSurface = await createRequiredSurfaceInstance(
    itemSurfaceDraft,
    itemSurfaceTemplate,
    existingSurfaces,
  )

  const individualSurfaceTemplate =
    (individualSide === 'donor'
      ? contactTemplate.donor_surface_template
      : contactTemplate.recipient_surface_template) ?? null

  const contacts: Contact[] = []
  for (const individualId of individualIds) {
    const individualSurface = await saveSurfaceInstanceDraft(
      { individualId, conditionOfItemPartCategoryId: null, existingSurfaceId: null },
      individualSurfaceTemplate,
    )
    const donorSurfaceId = individualSide === 'donor' ? individualSurface?.id : itemSurface?.id
    const recipientSurfaceId =
      individualSide === 'recipient' ? individualSurface?.id : itemSurface?.id
    contacts.push(
      await createContact({
        contact_template_id: contactTemplate.id,
        donor_surface_id: donorSurfaceId ?? null,
        recipient_surface_id: recipientSurfaceId ?? null,
      }),
    )
  }
  return contacts
}
