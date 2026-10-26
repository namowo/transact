import { createSurfaceTemplate, updateSurfaceTemplate } from '@/api/surfaceTemplates'
import type { SurfaceTemplate } from '@/api/types'

export interface SurfaceTemplateDraft {
  // null until the user explicitly picks Individual or Item - the field
  // sections below only render once a kind is chosen. This "kind" only
  // decides which fields to show while planning; the individual/item
  // itself is entered later, during data entry, against the actual Surface.
  kind: 'individual' | 'item' | null
  locationOfBodyCategoryId: string | null
  bodyPartConditionCategoryId: string | null
  itemId: string | null
  itemPartsCategoryId: string | null
  conditionOfItemPartCategoryId: string | null
  surfaceMaterialCategoryId: string | null
  itemSurfaceMaterialCategoryId: string | null
  sourceOfDnaCategoryIds: string[]
  backgroundDna: boolean
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
    itemSurfaceMaterialCategoryId: null,
    sourceOfDnaCategoryIds: [],
    backgroundDna: false,
    furtherDescription: null,
  }
}

function inferSurfaceTemplateKind(template: SurfaceTemplate): 'individual' | 'item' | null {
  // item_id itself may be null even for an "item" template - the actual
  // item is chosen later, during data entry. Look at whichever category
  // fields are populated instead, since those are kind-specific.
  if (
    template.item_id != null ||
    template.item_parts_category_id != null ||
    template.condition_of_item_part_category_id != null
  ) {
    return 'item'
  }
  if (template.location_of_body_category_id != null || template.body_part_condition_category_id != null) {
    return 'individual'
  }
  // A saved template with only shared/individual-only fields set (surface
  // material, source of DNA, etc.) and no kind-specific data - default to
  // individual so the record's fields stay visible instead of being hidden
  // behind the "choose a kind" prompt.
  if (
    template.surface_material_category_id != null ||
    (template.source_of_dna_categories?.length ?? 0) > 0
  ) {
    return 'individual'
  }
  if (template.item_surface_material_category_id != null) {
    return 'item'
  }
  return null
}

export function surfaceTemplateDraftFromSurfaceTemplate(
  template: SurfaceTemplate | null | undefined,
): SurfaceTemplateDraft {
  if (!template) return emptySurfaceTemplateDraft()
  return {
    kind: inferSurfaceTemplateKind(template),
    locationOfBodyCategoryId: template.location_of_body_category_id ?? null,
    bodyPartConditionCategoryId: template.body_part_condition_category_id ?? null,
    itemId: template.item_id ?? null,
    itemPartsCategoryId: template.item_parts_category_id ?? null,
    conditionOfItemPartCategoryId: template.condition_of_item_part_category_id ?? null,
    surfaceMaterialCategoryId: template.surface_material_category_id ?? null,
    itemSurfaceMaterialCategoryId: template.item_surface_material_category_id ?? null,
    sourceOfDnaCategoryIds: (template.source_of_dna_categories ?? []).map((c) => c.id),
    backgroundDna: !!template.background_dna,
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
      draft.sourceOfDnaCategoryIds.length === 0
    )
  }
  return (
    !draft.itemId &&
    !draft.itemPartsCategoryId &&
    !draft.conditionOfItemPartCategoryId &&
    !draft.itemSurfaceMaterialCategoryId
  )
}

// Persists the SurfaceTemplate row, creating or updating it as needed.
// Returns null for a draft that's still entirely empty, so an unused
// donor/recipient slot doesn't produce a stray SurfaceTemplate row.
export async function saveSurfaceTemplateDraft(
  draft: SurfaceTemplateDraft,
  existingSurfaceTemplateId: string | null,
): Promise<string | null> {
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
    surface_material_category_id: draft.kind === 'individual' ? draft.surfaceMaterialCategoryId : null,
    item_surface_material_category_id:
      draft.kind === 'item' ? draft.itemSurfaceMaterialCategoryId : null,
    source_of_dna_category_ids: draft.kind === 'individual' ? draft.sourceOfDnaCategoryIds : [],
    background_dna: draft.backgroundDna,
    further_description_of_background_and_prevalence: draft.furtherDescription || null,
  }

  const template = existingSurfaceTemplateId
    ? await updateSurfaceTemplate(existingSurfaceTemplateId, payload)
    : await createSurfaceTemplate(payload)
  return template.id
}
