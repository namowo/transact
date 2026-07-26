import type { NamedCategory } from './categories'
import type { Individual } from './individual'
import type { SurfaceTemplate } from './surfaceTemplate'

// An actual, realized instance of a SurfaceTemplate: it links back to the
// template it instantiates and carries the Individual (for Individual-kind
// templates) or overrides (for Item-kind templates) entered during data
// entry. A null override means the template's value applies.
export interface Surface {
  id: number
  surface_template_id?: number | null
  surface_template?: SurfaceTemplate | null
  individual_id?: number | null
  individual?: Individual | null
  location_of_body_category_id?: number | null
  location_of_body_category?: NamedCategory | null
  body_part_condition_category_id?: number | null
  body_part_condition_category?: NamedCategory | null
  item_parts_category_id?: number | null
  item_parts_category?: NamedCategory | null
  condition_of_item_part_category_id?: number | null
  condition_of_item_part_category?: NamedCategory | null
  surface_material_category_id?: number | null
  surface_material_category?: NamedCategory | null
  source_of_dna_category_id?: number | null
  source_of_dna_category?: NamedCategory | null
}

export interface SurfaceInput {
  surface_template_id?: number | null
  individual_id?: number | null
  location_of_body_category_id?: number | null
  body_part_condition_category_id?: number | null
  item_parts_category_id?: number | null
  condition_of_item_part_category_id?: number | null
  surface_material_category_id?: number | null
  source_of_dna_category_id?: number | null
}
