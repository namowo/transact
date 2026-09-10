// Simple named lookup categories (id + name + description) shared by the
// scenario/contact/surface domain. All of these expose identical CRUD shape.
export interface NamedCategory {
  id: string
  name?: string | null
  description?: string | null
}

export interface NamedCategoryInput {
  name?: string | null
  description?: string | null
}

export interface SkinDiseaseCategory {
  id: string
  name?: string | null
  influence_on_shedding_propensity?: boolean | null
  literature?: string | null
}

export interface SkinDiseaseCategoryInput {
  name?: string | null
  influence_on_shedding_propensity?: boolean | null
  literature?: string | null
}

// Unlike other named categories, an item subcategory belongs to exactly one
// item category - the picker only offers subcategories once a category has
// been chosen, and new subcategories are always created under that category.
export interface ItemSubcategory {
  id: string
  name?: string | null
  description?: string | null
  item_category_id?: string | null
}

export interface ItemSubcategoryInput {
  name?: string | null
  description?: string | null
  item_category_id?: string | null
}

export interface TypeOfSwabCategory {
  id: string
  name?: string | null
  description?: string | null
  supplier_id?: string | null
  supplier?: Supplier | null
}

// Shared by cutting/picking/scraping/tape/vacuum methods and type-of-swab, so
// supplier names/catalogue entries aren't duplicated per method.
export interface Supplier {
  id: string
  name?: string | null
  catalogue_number_of_supplier?: string | null
  full_name_as_by_supplier?: string | null
}

export interface SupplierInput {
  name?: string | null
  catalogue_number_of_supplier?: string | null
  full_name_as_by_supplier?: string | null
}

// A literature reference describing how shedding propensity was determined
// in a study, not a simple named category - it carries its own bibliography
// and methodology fields.
export interface DeterminationOfSheddingPropensityCategory {
  id: string
  authors?: string | null
  title?: string | null
  doi?: string | null
  restrictions_prior_to_sampling?: string | null
  monitored_transfer_factors?: string | null
  number_of_participants?: string | null
  replicates?: string | null
  shedder_test?: string | null
  classification_criteria?: string | null
  classification_scheme?: string | null
  classification_outcome?: string | null
}

export interface DeterminationOfSheddingPropensityCategoryInput {
  authors?: string | null
  title?: string | null
  doi?: string | null
  restrictions_prior_to_sampling?: string | null
  monitored_transfer_factors?: string | null
  number_of_participants?: string | null
  replicates?: string | null
  shedder_test?: string | null
  classification_criteria?: string | null
  classification_scheme?: string | null
  classification_outcome?: string | null
}
