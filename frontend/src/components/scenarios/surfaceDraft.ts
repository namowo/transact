import { createSurface, updateSurface } from '@/api/surfaces'
import type { Surface } from '@/api/types'

export interface SurfaceDraft {
  // null until the user explicitly picks Individual or Item - the field
  // sections below only render once a kind is chosen.
  kind: 'individual' | 'item' | null
  // The Individual/Item record itself is created/edited entirely through
  // IndividualSelect/ItemSelect's own dialogs; this draft only needs to
  // remember which one is linked to the surface.
  individualId: number | null
  locationOfBodyCategoryId: number | null
  bodyPartConditionCategoryId: number | null
  itemId: number | null
  itemPartsCategoryId: number | null
  conditionOfItemPartCategoryId: number | null
  surfaceMaterialCategoryId: number | null
  sourceOfDnaCategoryId: number | null
  backgroundDna: boolean
  prevalence: boolean
  furtherDescription: string | null
}

export function emptySurfaceDraft(): SurfaceDraft {
  return {
    kind: null,
    individualId: null,
    locationOfBodyCategoryId: null,
    bodyPartConditionCategoryId: null,
    itemId: null,
    itemPartsCategoryId: null,
    conditionOfItemPartCategoryId: null,
    surfaceMaterialCategoryId: null,
    sourceOfDnaCategoryId: null,
    backgroundDna: false,
    prevalence: false,
    furtherDescription: null,
  }
}

export function surfaceDraftFromSurface(surface: Surface | null | undefined): SurfaceDraft {
  if (!surface) return emptySurfaceDraft()
  return {
    kind: surface.item_id ? 'item' : 'individual',
    individualId: surface.individual_id ?? null,
    locationOfBodyCategoryId: surface.location_of_body_category_id ?? null,
    bodyPartConditionCategoryId: surface.body_part_condition_category_id ?? null,
    itemId: surface.item_id ?? null,
    itemPartsCategoryId: surface.item_parts_category_id ?? null,
    conditionOfItemPartCategoryId: surface.condition_of_item_part_category_id ?? null,
    surfaceMaterialCategoryId: surface.surface_material_category_id ?? null,
    sourceOfDnaCategoryId: surface.source_of_dna_category_id ?? null,
    backgroundDna: !!surface.background_dna,
    prevalence: !!surface.prevalence,
    furtherDescription: surface.further_description_of_background_and_prevalence ?? null,
  }
}

function isBlankDraft(draft: SurfaceDraft): boolean {
  if (draft.kind === null) return true
  if (draft.kind === 'individual') {
    return (
      !draft.individualId &&
      !draft.locationOfBodyCategoryId &&
      !draft.bodyPartConditionCategoryId &&
      !draft.surfaceMaterialCategoryId &&
      !draft.sourceOfDnaCategoryId
    )
  }
  return (
    !draft.itemId &&
    !draft.itemPartsCategoryId &&
    !draft.conditionOfItemPartCategoryId &&
    !draft.surfaceMaterialCategoryId &&
    !draft.sourceOfDnaCategoryId
  )
}

// Persists the Surface row, creating or updating it as needed - the
// Individual/Item it links to is saved directly by IndividualSelect /
// ItemSelect. Returns null for a draft that's still entirely empty, so an
// unused donor/recipient slot doesn't produce a stray Surface row.
export async function saveSurfaceDraft(
  draft: SurfaceDraft,
  existingSurfaceId: number | null,
): Promise<number | null> {
  if (isBlankDraft(draft)) return existingSurfaceId

  const surfacePayload = {
    individual_id: draft.kind === 'individual' ? draft.individualId : null,
    item_id: draft.kind === 'item' ? draft.itemId : null,
    location_of_body_category_id:
      draft.kind === 'individual' ? draft.locationOfBodyCategoryId : null,
    body_part_condition_category_id:
      draft.kind === 'individual' ? draft.bodyPartConditionCategoryId : null,
    item_parts_category_id: draft.kind === 'item' ? draft.itemPartsCategoryId : null,
    condition_of_item_part_category_id:
      draft.kind === 'item' ? draft.conditionOfItemPartCategoryId : null,
    surface_material_category_id: draft.surfaceMaterialCategoryId,
    source_of_dna_category_id: draft.sourceOfDnaCategoryId,
    background_dna: draft.backgroundDna,
    prevalence: draft.prevalence,
    further_description_of_background_and_prevalence: draft.furtherDescription || null,
  }

  const surface = existingSurfaceId
    ? await updateSurface(existingSurfaceId, surfacePayload)
    : await createSurface(surfacePayload)
  return surface.id
}
