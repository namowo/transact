import { createSurface } from '@/api/surfaces'
import type { Surface, SurfaceTemplate } from '@/api/types'

// Fills in a SurfaceTemplate slot with a real Individual or Item to produce
// an actual Surface. By default each actual Contact gets its own
// freshly-created Surface row per slot, but setting existingSurfaceId
// reuses a Surface already created for an earlier Contact instead - needed
// to chain contacts (e.g. the item surface a donor touched is the same one
// later touched by a recipient).
export interface SurfaceInstanceDraft {
  individualId: string | null
  conditionOfItemPartCategoryId: string | null
  existingSurfaceId: string | null
}

export function emptySurfaceInstanceDraft(): SurfaceInstanceDraft {
  return {
    individualId: null,
    conditionOfItemPartCategoryId: null,
    existingSurfaceId: null,
  }
}

function isBlankDraft(draft: SurfaceInstanceDraft): boolean {
  return (
    draft.individualId === null &&
    draft.conditionOfItemPartCategoryId === null &&
    draft.existingSurfaceId === null
  )
}

// Creates a Surface instantiating the given template, or returns the
// existing one the draft points to when reusing a prior Contact's surface.
// Returns null when the template itself is missing or the draft is entirely
// blank, so an unused slot doesn't produce a stray Surface row.
export async function saveSurfaceInstanceDraft(
  draft: SurfaceInstanceDraft,
  template: SurfaceTemplate | null,
  existingSurfaces?: Surface[],
): Promise<Surface | null> {
  if (!template || isBlankDraft(draft)) return null
  if (draft.existingSurfaceId) {
    return existingSurfaces?.find((s) => s.id === draft.existingSurfaceId) ?? null
  }
  return createSurfaceInstance(draft, template)
}

// Like saveSurfaceInstanceDraft, but always creates/returns a Surface when a
// template is given, even if the draft has no overrides. Needed for an
// item-side slot that other Surfaces (e.g. a batch of individuals) need to
// reference - unlike the single-pair flow, skipping creation here would
// leave those contacts with no surface on that side at all.
export async function createRequiredSurfaceInstance(
  draft: SurfaceInstanceDraft,
  template: SurfaceTemplate | null,
  existingSurfaces?: Surface[],
): Promise<Surface | null> {
  if (!template) return null
  if (draft.existingSurfaceId) {
    return existingSurfaces?.find((s) => s.id === draft.existingSurfaceId) ?? null
  }
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
