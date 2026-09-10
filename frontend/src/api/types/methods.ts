import type { Laboratory } from './laboratory'
import type { NamedCategory, Supplier } from './categories'

// Laboratory-scoped methods -------------------------------------------------

export interface ExtractionMethod {
  id: string
  laboratory_id?: string | null
  laboratory?: Laboratory | null
  principle_of_extraction_method_category_id?: string | null
  principle_of_extraction_method_category?: NamedCategory | null
  extraction_protocol?: string | null
  extraction_platform_id?: string | null
  extraction_platform?: NamedCategory | null
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
  id: string
  laboratory_id?: string | null
  laboratory?: Laboratory | null
  pcr_kit_id?: string | null
  pcr_kit?: NamedCategory | null
  thermocycler_id?: string | null
  thermocycler?: NamedCategory | null
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
  id: string
  laboratory_id?: string | null
  laboratory?: Laboratory | null
  ce_device_id?: string | null
  ce_device?: NamedCategory | null
  application_type?: string | null
  capillary_length?: number | null
  polymer_id?: string | null
  polymer?: NamedCategory | null
  dye_set_id?: string | null
  dye_set?: NamedCategory | null
  oven_temperature?: number | null
  run_voltage?: number | null
  pre_run_voltage?: number | null
  injection_voltage?: number | null
  run_time?: string | null
  pre_run_time?: string | null
  injection_time?: string | null
  type_of_formamide_id?: string | null
  type_of_formamide?: NamedCategory | null
  volume_formamide?: number | null
  size_standard_id?: string | null
  size_standard?: NamedCategory | null
  volume_size_standard?: number | null
  input_volume_pcr_product?: number | null
  final_volume?: number | null
}

export type CEMethodInput = Omit<CEMethod, 'id' | 'laboratory'>

export interface QuantificationMethod {
  id: string
  laboratory_id?: string | null
  laboratory?: Laboratory | null
  principle_of_quant_method_category_id?: string | null
  principle_of_quant_method_category?: NamedCategory | null
  kit_id?: string | null
  kit?: NamedCategory | null
  manufacturer_id?: string | null
  manufacturer?: NamedCategory | null
  platform_id?: string | null
  platform?: NamedCategory | null
  description_of_protocol?: string | null
  abbreviations_to_manufacturers_protocol?: string | null
}

export type QuantificationMethodInput = Omit<
  QuantificationMethod,
  'id' | 'laboratory' | 'principle_of_quant_method_category'
>

export interface EPGAnalysisMethod {
  id: string
  laboratory_id?: string | null
  laboratory?: Laboratory | null
  genotyping_software_id?: string | null
  genotyping_software?: NamedCategory | null
  analytical_threshold?: number | null
  application_analytical_threshold?: string | null
  stutter_filter?: string | null
}

export type EPGAnalysisMethodInput = Omit<EPGAnalysisMethod, 'id' | 'laboratory'>

export interface EPGInterpretationMethod {
  id: string
  laboratory_id?: string | null
  laboratory?: Laboratory | null
  determination_of_noc?: string | null
  statistical_software_id?: string | null
  statistical_software?: NamedCategory | null
  parameters_modelled_by_software?: string | null
  allele_frequency_database?: string | null
}

export type EPGInterpretationMethodInput = Omit<EPGInterpretationMethod, 'id' | 'laboratory'>

export interface PostPCRTreatmentMethod {
  id: string
  laboratory_id?: string | null
  laboratory?: Laboratory | null
  application_of_post_pcr_purification_step?: boolean | null
  description_of_post_pcr_purification_step?: string | null
  dilution_of_pcr_product?: boolean | null
  dilution_factor?: number | null
}

export type PostPCRTreatmentMethodInput = Omit<PostPCRTreatmentMethod, 'id' | 'laboratory'>

// Device/category-scoped sub-methods ----------------------------------------

export interface SwabMethod {
  id: string
  wetting_agent_id?: string | null
  wetting_agent?: NamedCategory | null
  volume_of_wetting_agent?: number | null
  specification?: string | null
  description?: string | null
  type_of_swab_category_id?: string | null
  type_of_swab_category?: NamedCategory | null
  swabbing_technique_category_id?: string | null
  swabbing_technique_category?: NamedCategory | null
}

export type SwabMethodInput = Omit<
  SwabMethod,
  'id' | 'type_of_swab_category' | 'swabbing_technique_category'
>

export interface TapeMethod {
  id: string
  type_of_tape_id?: string | null
  type_of_tape?: NamedCategory | null
  description?: string | null
  supplier_id?: string | null
  supplier?: Supplier | null
}

export type TapeMethodInput = Omit<TapeMethod, 'id' | 'type_of_tape'>

export interface VacuumMethod {
  id: string
  vacuum_device_id?: string | null
  vacuum_device?: NamedCategory | null
  description?: string | null
  supplier_id?: string | null
  supplier?: Supplier | null
}

export type VacuumMethodInput = Omit<VacuumMethod, 'id' | 'vacuum_device'>

export interface CuttingMethod {
  id: string
  cutting_device_id?: string | null
  cutting_device?: NamedCategory | null
  description?: string | null
  supplier_id?: string | null
  supplier?: Supplier | null
}

export type CuttingMethodInput = Omit<CuttingMethod, 'id' | 'cutting_device'>

export interface ScrapingMethod {
  id: string
  scraping_device_id?: string | null
  scraping_device?: NamedCategory | null
  description?: string | null
  supplier_id?: string | null
  supplier?: Supplier | null
}

export type ScrapingMethodInput = Omit<ScrapingMethod, 'id' | 'scraping_device'>

export interface PickingMethod {
  id: string
  picking_device_id?: string | null
  picking_device?: NamedCategory | null
  description?: string | null
  supplier_id?: string | null
  supplier?: Supplier | null
}

export type PickingMethodInput = Omit<PickingMethod, 'id' | 'picking_device'>

// Composite sampling method ---------------------------------------------------

export interface SamplingMethod {
  id: string
  laboratory_id?: string | null
  laboratory?: Laboratory | null
  swab_method_id?: string | null
  swab_method?: SwabMethod | null
  tape_method_id?: string | null
  tape_method?: TapeMethod | null
  vacuum_method_id?: string | null
  vacuum_method?: VacuumMethod | null
  cutting_method_id?: string | null
  cutting_method?: CuttingMethod | null
  scraping_method_id?: string | null
  scraping_method?: ScrapingMethod | null
  picking_method_id?: string | null
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
