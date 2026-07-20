import type { DeterminationOfSheddingPropensityCategory, SkinDiseaseCategory } from './categories'

export interface Individual {
  id: number
  sex?: string | null
  age?: number | null
  dna_shedding_propensity?: string | null
  skin_disease_category_id?: number | null
  skin_disease_category?: SkinDiseaseCategory | null
  determination_of_shedding_propensity_category_id?: number | null
  determination_of_shedding_propensity_category?: DeterminationOfSheddingPropensityCategory | null
}

export interface IndividualInput {
  sex?: string | null
  age?: number | null
  dna_shedding_propensity?: string | null
  skin_disease_category_id?: number | null
  determination_of_shedding_propensity_category_id?: number | null
}
