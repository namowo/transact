// Simple named lookup categories (id + name + description) shared by the
// scenario/contact/surface domain. All of these expose identical CRUD shape.
export interface NamedCategory {
  id: number
  name?: string | null
  description?: string | null
}

export interface NamedCategoryInput {
  name?: string | null
  description?: string | null
}

export interface SkinDiseaseCategory {
  id: number
  name?: string | null
  influence_on_shedding_propensity?: boolean | null
  literature?: string | null
}

export interface SkinDiseaseCategoryInput {
  name?: string | null
  influence_on_shedding_propensity?: boolean | null
  literature?: string | null
}

export interface TypeOfSwabCategory {
  id: number
  name?: string | null
  catalogue_number_of_supplier?: string | null
  full_name_as_by_supplier?: string | null
  description?: string | null
  supplier?: string | null
}

// A literature reference describing how shedding propensity was determined
// in a study, not a simple named category - it carries its own bibliography
// and methodology fields.
export interface DeterminationOfSheddingPropensityCategory {
  id: number
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
