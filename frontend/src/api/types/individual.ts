import type {
  DeterminationOfSheddingPropensityCategory,
  NamedCategory,
  SkinDiseaseCategory,
} from './categories'

export interface Individual {
  id: string
  sex_id?: string | null
  sex?: NamedCategory | null
  age?: number | null
  dna_shedding_propensity_category_id?: string | null
  dna_shedding_propensity_category?: NamedCategory | null
  skin_disease_category_id?: string | null
  skin_disease_category?: SkinDiseaseCategory | null
  determination_of_shedding_propensity_category_id?: string | null
  determination_of_shedding_propensity_category?: DeterminationOfSheddingPropensityCategory | null
}

export interface IndividualInput {
  sex_id?: string | null
  age?: number | null
  dna_shedding_propensity_category_id?: string | null
  skin_disease_category_id?: string | null
  determination_of_shedding_propensity_category_id?: string | null
}
