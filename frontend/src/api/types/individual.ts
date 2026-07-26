import type {
  DeterminationOfSheddingPropensityCategory,
  NamedCategory,
  SkinDiseaseCategory,
} from './categories'

export interface Individual {
  id: number
  sex_id?: number | null
  sex?: NamedCategory | null
  age?: number | null
  dna_shedding_propensity_category_id?: number | null
  dna_shedding_propensity_category?: NamedCategory | null
  skin_disease_category_id?: number | null
  skin_disease_category?: SkinDiseaseCategory | null
  determination_of_shedding_propensity_category_id?: number | null
  determination_of_shedding_propensity_category?: DeterminationOfSheddingPropensityCategory | null
}

export interface IndividualInput {
  sex_id?: number | null
  age?: number | null
  dna_shedding_propensity_category_id?: number | null
  skin_disease_category_id?: number | null
  determination_of_shedding_propensity_category_id?: number | null
}
