import { createSurfaceTemplate, updateSurfaceTemplate } from '@/api/surfaceTemplates'
import type { SurfaceTemplate } from '@/api/types'

export interface SurfaceTemplateDraft {
  // null until the user explicitly picks Individual or Item - the field
  // sections below only render once a kind is chosen. This "kind" only
  // decides which fields to show while planning; the individual/item
  // itself is entered later, during data entry, against the actual Surface.
  kind: 'individual' | 'item' | null
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

export function emptySurfaceTemplateDraft(): SurfaceTemplateDraft {
  return {
    kind: null,
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

export function surfaceTemplateDraftFromSurfaceTemplate(
  template: SurfaceTemplate | null | undefined,
): SurfaceTemplateDraft {
  if (!template) return emptySurfaceTemplateDraft()
  return {
    kind: template.item_id ? 'item' : 'individual',
    locationOfBodyCategoryId: template.location_of_body_category_id ?? null,
    bodyPartConditionCategoryId: template.body_part_condition_category_id ?? null,
    itemId: template.item_id ?? null,
    itemPartsCategoryId: template.item_parts_category_id ?? null,
    conditionOfItemPartCategoryId: template.condition_of_item_part_category_id ?? null,
    surfaceMaterialCategoryId: template.surface_material_category_id ?? null,
    sourceOfDnaCategoryId: template.source_of_dna_category_id ?? null,
    backgroundDna: !!template.background_dna,
    prevalence: !!template.prevalence,
    furtherDescription: template.further_description_of_background_and_prevalence ?? null,
  }
}

function isBlankDraft(draft: SurfaceTemplateDraft): boolean {
  if (draft.kind === null) return true
  if (draft.kind === 'individual') {
    return (
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

// Persists the SurfaceTemplate row, creating or updating it as needed.
// Returns null for a draft that's still entirely empty, so an unused
// donor/recipient slot doesn't produce a stray SurfaceTemplate row.
export async function saveSurfaceTemplateDraft(
  draft: SurfaceTemplateDraft,
  existingSurfaceTemplateId: number | null,
): Promise<number | null> {
  if (isBlankDraft(draft)) return existingSurfaceTemplateId

  const payload = {
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

  const template = existingSurfaceTemplateId
    ? await updateSurfaceTemplate(existingSurfaceTemplateId, payload)
    : await createSurfaceTemplate(payload)
  return template.id
}
