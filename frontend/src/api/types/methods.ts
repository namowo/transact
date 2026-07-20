import type { Laboratory } from './laboratory'
import type { NamedCategory } from './categories'

// Laboratory-scoped methods -------------------------------------------------

export interface ExtractionMethod {
  id: number
  laboratory_id?: number | null
  laboratory?: Laboratory | null
  principle_of_extraction_method_category_id?: number | null
  principle_of_extraction_method_category?: NamedCategory | null
  extraction_protocol?: string | null
  extraction_platform?: string | null
  additional_lysis_buffer_components?: string | null
  volume_lysis_buffer_components?: number | null
  lysis_incubation_time?: string | null
  lysis_incubation_temperature?: number | null
  volume_of_lysate_used_for_extraction?: number | null
  application_of_further_purification_step?: boolean | null
  description_of_further_purification_step?: string | null
}

export type ExtractionMethodInput = Omit<
  ExtractionMethod,
  'id' | 'laboratory' | 'principle_of_extraction_method_category'
>

export interface PCRMethod {
  id: number
  laboratory_id?: number | null
  laboratory?: Laboratory | null
  pcr_kit?: string | null
  thermocycler?: string | null
  initial_denaturation_temp?: number | null
  initial_denaturation_time?: string | null
  no_of_cycles?: number | null
  denaturation_temp?: number | null
  denaturation_time?: string | null
  annealing_temp?: number | null
  annealing_time?: string | null
  elongation_temp?: number | null
  elongation_time?: string | null
  final_elongation_temp?: number | null
  final_elongation_time?: string | null
  ramping?: number | null
  total_volume_pcr_reaction?: number | null
}

export type PCRMethodInput = Omit<PCRMethod, 'id' | 'laboratory'>

export interface CEMethod {
  id: number
  laboratory_id?: number | null
  laboratory?: Laboratory | null
  ce_device?: string | null
  application_type?: string | null
  capillary_length?: number | null
  polymer?: string | null
  dye_set?: string | null
  oven_temperature?: number | null
  run_voltage?: number | null
  pre_run_voltage?: number | null
  injection_voltage?: number | null
  run_time?: string | null
  pre_run_time?: string | null
  injection_time?: string | null
  type_of_formamide?: string | null
  volume_formamide?: number | null
  size_standard?: string | null
  volume_size_standard?: number | null
  input_volume_pcr_product?: number | null
  final_volume?: number | null
}

export type CEMethodInput = Omit<CEMethod, 'id' | 'laboratory'>

export interface QuantificationMethod {
  id: number
  laboratory_id?: number | null
  laboratory?: Laboratory | null
  principle_of_quant_method_category_id?: number | null
  principle_of_quant_method_category?: NamedCategory | null
  kit?: string | null
  manufacturer?: string | null
  platform?: string | null
  description_of_protocol?: string | null
  abbreviations_to_manufacturers_protocol?: string | null
}

export type QuantificationMethodInput = Omit<
  QuantificationMethod,
  'id' | 'laboratory' | 'principle_of_quant_method_category'
>

export interface EPGAnalysisMethod {
  id: number
  laboratory_id?: number | null
  laboratory?: Laboratory | null
  genotyping_software?: string | null
  analytical_threshold?: number | null
  application_analytical_threshold?: string | null
  stutter_filter?: string | null
}

export type EPGAnalysisMethodInput = Omit<EPGAnalysisMethod, 'id' | 'laboratory'>

export interface EPGInterpretationMethod {
  id: number
  laboratory_id?: number | null
  laboratory?: Laboratory | null
  determination_of_noc?: string | null
  statistical_software?: string | null
  parameters_modelled_by_software?: string | null
  allele_frequency_database?: string | null
}

export type EPGInterpretationMethodInput = Omit<EPGInterpretationMethod, 'id' | 'laboratory'>

export interface PostPCRTreatmentMethod {
  id: number
  laboratory_id?: number | null
  laboratory?: Laboratory | null
  application_of_post_pcr_purification_step?: boolean | null
  description_of_post_pcr_purification_step?: string | null
  dilution_of_pcr_product?: boolean | null
  dilution_factor?: number | null
}

export type PostPCRTreatmentMethodInput = Omit<PostPCRTreatmentMethod, 'id' | 'laboratory'>

// Device/category-scoped sub-methods ----------------------------------------

export interface SwabMethod {
  id: number
  wetting_agent?: string | null
  volume_of_wetting_agent?: number | null
  specification?: string | null
  description?: string | null
  type_of_swab_category_id?: number | null
  type_of_swab_category?: NamedCategory | null
  swabbing_technique_category_id?: number | null
  swabbing_technique_category?: NamedCategory | null
}

export type SwabMethodInput = Omit<
  SwabMethod,
  'id' | 'type_of_swab_category' | 'swabbing_technique_category'
>

export interface TapeMethod {
  id: number
  type_of_tape_id?: number | null
  type_of_tape?: NamedCategory | null
  description?: string | null
  catalogue_number_of_supplier?: string | null
  full_name_as_by_supplier?: string | null
  supplier?: string | null
}

export type TapeMethodInput = Omit<TapeMethod, 'id' | 'type_of_tape'>

export interface VacuumMethod {
  id: number
  vacuum_device_id?: number | null
  vacuum_device?: NamedCategory | null
  description?: string | null
  catalogue_number_of_supplier?: string | null
  full_name_as_by_supplier?: string | null
  supplier?: string | null
}

export type VacuumMethodInput = Omit<VacuumMethod, 'id' | 'vacuum_device'>

export interface CuttingMethod {
  id: number
  cutting_device_id?: number | null
  cutting_device?: NamedCategory | null
  description?: string | null
  catalogue_number_of_supplier?: string | null
  full_name_as_by_supplier?: string | null
  supplier?: string | null
}

export type CuttingMethodInput = Omit<CuttingMethod, 'id' | 'cutting_device'>

export interface ScrapingMethod {
  id: number
  scraping_device_id?: number | null
  scraping_device?: NamedCategory | null
  description?: string | null
  catalogue_number_of_supplier?: string | null
  full_name_as_by_supplier?: string | null
  supplier?: string | null
}

export type ScrapingMethodInput = Omit<ScrapingMethod, 'id' | 'scraping_device'>

export interface PickingMethod {
  id: number
  picking_device_id?: number | null
  picking_device?: NamedCategory | null
  description?: string | null
  catalogue_number_of_supplier?: string | null
  full_name_as_by_supplier?: string | null
  supplier?: string | null
}

export type PickingMethodInput = Omit<PickingMethod, 'id' | 'picking_device'>

// Composite sampling method ---------------------------------------------------

export interface SamplingMethod {
  id: number
  laboratory_id?: number | null
  laboratory?: Laboratory | null
  swab_method_id?: number | null
  swab_method?: SwabMethod | null
  tape_method_id?: number | null
  tape_method?: TapeMethod | null
  vacuum_method_id?: number | null
  vacuum_method?: VacuumMethod | null
  cutting_method_id?: number | null
  cutting_method?: CuttingMethod | null
  scraping_method_id?: number | null
  scraping_method?: ScrapingMethod | null
  picking_method_id?: number | null
  picking_method?: PickingMethod | null
}

export type SamplingMethodInput = Omit<
  SamplingMethod,
  | 'id'
  | 'laboratory'
  | 'swab_method'
  | 'tape_method'
  | 'vacuum_method'
  | 'cutting_method'
  | 'scraping_method'
  | 'picking_method'
>
