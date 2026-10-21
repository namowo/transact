import { createSurface } from '@/api/surfaces'
import type { Surface, SurfaceTemplate } from '@/api/types'

// Fills in a SurfaceTemplate slot with a real Individual or Item to produce
// an actual Surface. Every actual Contact gets its own freshly-created
// Surface rows per slot, even if the same Individual/Item is reused across
// multiple contacts.
export interface SurfaceInstanceDraft {
  individualId: string | null
  conditionOfItemPartCategoryId: string | null
}

export function emptySurfaceInstanceDraft(): SurfaceInstanceDraft {
  return {
    individualId: null,
    conditionOfItemPartCategoryId: null,
  }
}

function isBlankDraft(draft: SurfaceInstanceDraft): boolean {
  return draft.individualId === null && draft.conditionOfItemPartCategoryId === null
}

// Creates a Surface instantiating the given template. Returns null when the
// template itself is missing or the draft is entirely blank, so an unused
// slot doesn't produce a stray Surface row.
export async function saveSurfaceInstanceDraft(
  draft: SurfaceInstanceDraft,
  template: SurfaceTemplate | null,
): Promise<Surface | null> {
  if (!template || isBlankDraft(draft)) return null
  return createSurfaceInstance(draft, template)
}

// Like saveSurfaceInstanceDraft, but always creates the Surface when a
// template is given, even if the draft has no overrides. Needed for an
// item-side slot that other Surfaces (e.g. a batch of individuals) need to
// reference - unlike the single-pair flow, skipping creation here would
// leave those contacts with no surface on that side at all.
export async function createRequiredSurfaceInstance(
  draft: SurfaceInstanceDraft,
  template: SurfaceTemplate | null,
): Promise<Surface | null> {
  if (!template) return null
  return createSurfaceInstance(draft, template)
}

function createSurfaceInstance(draft: SurfaceInstanceDraft, template: SurfaceTemplate): Promise<Surface> {
  const isIndividual = !template.item_id
  return createSurface({
    surface_template_id: template.id,
    individual_id: isIndividual ? draft.individualId : null,
    condition_of_item_part_category_id: isIndividual
      ? null
      : draft.conditionOfItemPartCategoryId,
  })
}
