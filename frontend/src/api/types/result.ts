import type { NamedCategory } from './categories'
import type { Individual } from './individual'
import type { RecoverySet } from './recoverySet'
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
  id: string
  name?: string | null
  study_id?: string | null
  recovery_set_id?: string | null
  recovery_set?: RecoverySet | null
  surface_id?: string | null
  surface?: Surface | null
  sampling_method_id?: string | null
  sampling_method?: SamplingMethod | null
  extraction_method_id?: string | null
  extraction_method?: ExtractionMethod | null
  elution_volume?: number | null
  area?: number | null
  experience_level_of_sampler_id?: string | null
  experience_level_of_sampler?: NamedCategory | null
}

export interface RecoveryInput {
  name: string | null
  study_id: string | null
  recovery_set_id: string | null
  surface_id: string | null
  sampling_method_id: string | null
  extraction_method_id: string | null
  elution_volume: number | null
  area: number | null
  experience_level_of_sampler_id: string | null
}

// One contributor (a known Individual, or an unknown person like "UP1") to
// a PCR run's mixture, each with their own proportion. How many of these
// exist is driven by the PCR run's no_of_contributors.
export interface PCRContributor {
  id: string
  individual_id?: string | null
  individual?: Individual | null
  unknown_label?: string | null
  mixture_proportion?: number | null
}

export interface PCRContributorInput {
  individual_id: string | null
  unknown_label: string | null
  mixture_proportion: number | null
}

// One genotyping result run off a Result's quantified extract. A Result
// can have several (re-runs, replicates), so these are kept as
// Result.pcrs rather than flattened onto Result itself.
export interface PCR {
  id: string
  pcr_method_id?: string | null
  pcr_method?: PCRMethod | null
  sample_input_volume_in_pcr?: number | null
  dna_input_amount_in_pcr?: number | null
  post_pcr_treatment_method_id?: string | null
  post_pcr_treatment_method?: PostPCRTreatmentMethod | null
  ce_method_id?: string | null
  ce_method?: CEMethod | null
  epg_analysis_method_id?: string | null
  epg_analysis_method?: EPGAnalysisMethod | null
  epg_interpretation_method_id?: string | null
  epg_interpretation_method?: EPGInterpretationMethod | null
  no_of_contributors?: number | null
  total_rfu?: number | null
  total_no_of_alleles?: number | null
  contributors: PCRContributor[]
}

export interface PCRInput {
  pcr_method_id: string | null
  sample_input_volume_in_pcr: number | null
  dna_input_amount_in_pcr: number | null
  post_pcr_treatment_method_id: string | null
  ce_method_id: string | null
  epg_analysis_method_id: string | null
  epg_interpretation_method_id: string | null
  no_of_contributors: number | null
  total_rfu: number | null
  total_no_of_alleles: number | null
  contributors: PCRContributorInput[]
}

export interface Result {
  id: string
  recovery_id?: string | null
  recovery?: Recovery | null
  quantification_method_id?: string | null
  quantification_method?: QuantificationMethod | null
  dna_concentration?: number | null
  // Derived server-side as dna_concentration × recovery.elution_volume.
  dna_quantity?: number | null
  degradation_category_id?: string | null
  degradation_category?: NamedCategory | null
  inhibition_category_id?: string | null
  inhibition_category?: NamedCategory | null
  pcrs: PCR[]
}

export interface ResultInput {
  recovery_id: string | null
  quantification_method_id: string | null
  dna_concentration: number | null
  degradation_category_id: string | null
  inhibition_category_id: string | null
  // Full-replace on save: omit to leave the backend's existing PCRs
  // untouched, or pass the complete list to replace them.
  pcrs?: PCRInput[]
}
