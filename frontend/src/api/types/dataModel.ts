export type FieldType = 'string' | 'category' | 'number' | 'boolean' | 'date'

export type FilterOp =
  | 'eq'
  | 'neq'
  | 'in'
  | 'not_in'
  | 'contains'
  | 'gt'
  | 'gte'
  | 'lt'
  | 'lte'
  | 'between'
  | 'is_null'
  | 'not_null'

export interface CatalogTable {
  key: string
  label: string
  description: string
  // Tables that are joined along with this one.
  requires: string[]
  // Always joined: the row's own table and the path to its study.
  required: boolean
}

export interface CatalogField {
  key: string
  label: string
  group: string
  table: string
  type: FieldType
  description?: string | null
  unit?: string | null
}

export interface CatalogDataset {
  key: string
  label: string
  description: string
  default_sort: string[]
  tables: CatalogTable[]
  fields: CatalogField[]
}

export interface Catalog {
  datasets: CatalogDataset[]
  operators: Record<FieldType, FilterOp[]>
}

export type FilterValue = string | number | boolean | null | (string | number | null)[]

export interface DataModelFilter {
  field: string
  op: FilterOp
  value?: FilterValue
}

export interface DataModelSort {
  field: string
  dir: 'asc' | 'desc'
}

export interface DataModelDefinition {
  dataset: string
  // Optional tables joined onto the rows. null: inferred from the fields
  // used (older models and share links).
  joins: string[] | null
  columns: string[]
  filters: DataModelFilter[]
  // null: all studies available to the viewer.
  study_ids: string[] | null
  sort: DataModelSort[]
}

// 'local' models live in this browser only (guests).
export type DataModelSource = 'preset' | 'public' | 'mine' | 'local'

export interface DataModel {
  id: string
  name: string
  description?: string | null
  definition: DataModelDefinition
  is_public: boolean
  source: DataModelSource
  owner_name?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface DataModelSave {
  name: string
  description?: string | null
  definition: DataModelDefinition
  is_public?: boolean
}

export interface PreviewColumn {
  key: string
  label: string
  type: FieldType
  unit?: string | null
}

export interface DataModelPreview {
  columns: PreviewColumn[]
  rows: unknown[][]
  total_rows: number
  study_count: number
}

export interface DownloadableStudy {
  id: string
  title: string
  year?: string | null
  laboratory_name?: string | null
  authors: string[]
  journal?: string | null
  doi?: string | null
  scenario_count: number
  sample_count: number
  // false for the viewer's own lab's unpublished or unchecked studies.
  published: boolean
}

export type ExportFormat = 'csv' | 'xlsx'
