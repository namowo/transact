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

// Likewise, an item part belongs to exactly one item category - the picker
// only offers parts once an item (and thus its category) has been chosen,
// and new parts are always created under that category.
export interface ItemPartsCategory {
  id: string
  name?: string | null
  description?: string | null
  item_category_id?: string | null
}

export interface ItemPartsCategoryInput {
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
export interface DeterminationOfSheddingPropensityCategoryAuthor {
  id?: string
  title?: string | null
  first_name: string
  last_name: string
}

// A restriction prior to sampling or a shedder test, each with an optional
// duration in seconds.
export interface DeterminationOfSheddingPropensityCategoryRestriction {
  restriction_prior_to_sampling_id: string
  duration?: number | null
  restriction_prior_to_sampling?: NamedCategory | null
}

export interface DeterminationOfSheddingPropensityCategoryShedderTest {
  shedder_test_id: string
  duration?: number | null
  shedder_test?: NamedCategory | null
}

export interface DeterminationOfSheddingPropensityCategory {
  id: string
  title?: string | null
  doi?: string | null
  authors?: DeterminationOfSheddingPropensityCategoryAuthor[]
  restrictions?: DeterminationOfSheddingPropensityCategoryRestriction[]
  monitored_transfer_factors?: NamedCategory[]
  number_of_participants?: number | null
  replicates?: number | null
  shedder_tests?: DeterminationOfSheddingPropensityCategoryShedderTest[]
  classification_criteria_id?: string | null
  classification_criteria?: NamedCategory | null
  classification_scheme_id?: string | null
  classification_scheme?: NamedCategory | null
  classification_outcome?: string | null
}

export interface DeterminationOfSheddingPropensityCategoryInput {
  title?: string | null
  doi?: string | null
  authors?: Omit<DeterminationOfSheddingPropensityCategoryAuthor, 'id'>[]
  restrictions?: { restriction_prior_to_sampling_id: string; duration?: number | null }[]
  monitored_transfer_factor_ids?: string[]
  number_of_participants?: number | null
  replicates?: number | null
  shedder_tests?: { shedder_test_id: string; duration?: number | null }[]
  classification_criteria_id?: string | null
  classification_scheme_id?: string | null
  classification_outcome?: string | null
}
