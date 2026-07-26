import type { NamedCategory } from './categories'
import type { Item } from './item'

export interface SurfaceTemplate {
  id: number
  location_of_body_category_id?: number | null
  location_of_body_category?: NamedCategory | null
  body_part_condition_category_id?: number | null
  body_part_condition_category?: NamedCategory | null
  item_id?: number | null
  item?: Item | null
  item_parts_category_id?: number | null
  item_parts_category?: NamedCategory | null
  condition_of_item_part_category_id?: number | null
  condition_of_item_part_category?: NamedCategory | null
  surface_material_category_id?: number | null
  surface_material_category?: NamedCategory | null
  source_of_dna_category_id?: number | null
  source_of_dna_category?: NamedCategory | null
  photo_path?: string | null
  background_dna?: boolean | null
  prevalence?: boolean | null
  further_description_of_background_and_prevalence?: string | null
}

export interface SurfaceTemplateInput {
  location_of_body_category_id?: number | null
  body_part_condition_category_id?: number | null
  item_id?: number | null
  item_parts_category_id?: number | null
  condition_of_item_part_category_id?: number | null
  surface_material_category_id?: number | null
  source_of_dna_category_id?: number | null
  photo_path?: string | null
  background_dna?: boolean | null
  prevalence?: boolean | null
  further_description_of_background_and_prevalence?: string | null
}
