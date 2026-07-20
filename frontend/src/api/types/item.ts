import type { NamedCategory } from './categories'

export interface Item {
  id: number
  item_category_id?: number | null
  item_category?: NamedCategory | null
  item_subcategory_id?: number | null
  item_subcategory?: NamedCategory | null
  description?: string | null
  picture_path?: string | null
}

export interface ItemInput {
  item_category_id?: number | null
  item_subcategory_id?: number | null
  description?: string | null
  picture_path?: string | null
}
