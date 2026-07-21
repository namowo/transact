import type { NamedCategory } from './categories'
import type { Surface } from './surface'
import type {
  CEMethod,
  EPGAnalysisMethod,
  EPGInterpretationMethod,
  ExtractionMethod,
  PCRMethod,
  PostPCRTreatmentMethod,
  QuantificationMethod,
  SamplingMethod,
} from './methods'

export interface Recovery {
  id: number
  surface_id?: number | null
  surface?: Surface | null
  sampling_method_id?: number | null
  sampling_method?: SamplingMethod | null
  extraction_method_id?: number | null
  extraction_method?: ExtractionMethod | null
  elution_volume?: number | null
  area?: number | null
  experience_level_of_sampler_id?: number | null
  experience_level_of_sampler?: NamedCategory | null
}

export interface RecoveryInput {
  surface_id: number | null
  sampling_method_id: number | null
  extraction_method_id: number | null
  elution_volume: number | null
  area: number | null
  experience_level_of_sampler_id: number | null
}

export interface Result {
  id: number
  recovery_id?: number | null
  recovery?: Recovery | null
  quantification_method_id?: number | null
  quantification_method?: QuantificationMethod | null
  dna_concentration?: number | null
  degradation?: string | null
  inhibition?: boolean | null
  dna_quantity?: number | null
  pcr_method_id?: number | null
  pcr_method?: PCRMethod | null
  sample_input_volume_in_pcr?: number | null
  dna_input_amount_in_pcr?: number | null
  post_pcr_treatment_method_id?: number | null
  post_pcr_treatment_method?: PostPCRTreatmentMethod | null
  ce_method_id?: number | null
  ce_method?: CEMethod | null
  epg_analysis_method_id?: number | null
  epg_analysis_method?: EPGAnalysisMethod | null
  epg_interpretation_method_id?: number | null
  epg_interpretation_method?: EPGInterpretationMethod | null
  no_of_contributors?: number | null
  mixture_proportion?: number | null
  total_rfu?: number | null
  total_no_of_alleles?: number | null
}

export interface ResultInput {
  recovery_id: number | null
  quantification_method_id: number | null
  dna_concentration: number | null
  degradation: string | null
  inhibition: boolean | null
  dna_quantity: number | null
  pcr_method_id: number | null
  sample_input_volume_in_pcr: number | null
  dna_input_amount_in_pcr: number | null
  post_pcr_treatment_method_id: number | null
  ce_method_id: number | null
  epg_analysis_method_id: number | null
  epg_interpretation_method_id: number | null
  no_of_contributors: number | null
  mixture_proportion: number | null
  total_rfu: number | null
  total_no_of_alleles: number | null
}
