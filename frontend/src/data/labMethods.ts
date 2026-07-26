import {
  ceMethodApi,
  cuttingMethodApi,
  epgAnalysisMethodApi,
  epgInterpretationMethodApi,
  extractionMethodApi,
  pcrMethodApi,
  pickingMethodApi,
  postPcrTreatmentMethodApi,
  quantificationMethodApi,
  scrapingMethodApi,
  swabMethodApi,
  tapeMethodApi,
  vacuumMethodApi,
} from '@/api/methods'
import {
  cuttingDeviceApi,
  pickingDeviceApi,
  principleOfExtractionMethodCategoryApi,
  principleOfQuantMethodCategoryApi,
  scrapingDeviceApi,
  swabbingTechniqueCategoryApi,
  typeOfSwabCategoryApi,
  typeOfTapeApi,
  vacuumDeviceApi,
  pcrKitApi,
  thermocyclerApi,
  ceDeviceApi,
  polymerApi,
  dyeSetApi,
  typeOfFormamideApi,
  sizeStandardApi,
  genotypingSoftwareApi,
  statisticalSoftwareApi,
  quantificationKitApi,
  manufacturerApi,
  platformApi,
  wettingAgentApi,
  supplierApi,
} from '@/api/categories'
import type { NamedCategory, NamedCategoryInput } from '@/api/types'

export type FieldType = 'text' | 'textarea' | 'number' | 'boolean' | 'category'

export interface MethodFieldConfig {
  key: string
  label: string
  type: FieldType
  // For 'category' fields: the dropdown's data source + create endpoint.
  categoryApi?: {
    list: () => Promise<NamedCategory[]>
    create: (payload: NamedCategoryInput) => Promise<NamedCategory>
  }
  // Column shown in the list table for this field (defaults to true for the
  // first few fields via `listColumns` below, not per-field).
}

export interface MethodConfig {
  key: string
  label: string
  api: {
    list: () => Promise<any[]>
    create: (payload: any) => Promise<any>
    update: (id: number, payload: any) => Promise<any>
    delete: (id: number) => Promise<void>
  }
  laboratoryScoped: boolean
  fields: MethodFieldConfig[]
  // Which field keys to show as DataTable columns (besides id).
  listColumns: string[]
}

export const labMethods: MethodConfig[] = [
  {
    key: 'extraction',
    label: 'Extraction',
    api: extractionMethodApi,
    laboratoryScoped: true,
    listColumns: ['extraction_protocol', 'extraction_platform'],
    fields: [
      {
        key: 'principle_of_extraction_method_category_id',
        label: 'Principle of extraction method',
        type: 'category',
        categoryApi: principleOfExtractionMethodCategoryApi,
      },
      { key: 'extraction_protocol', label: 'Extraction protocol', type: 'text' },
      {
        key: 'extraction_platform_id',
        label: 'Extraction platform',
        type: 'category',
        categoryApi: platformApi,
      },
      {
        key: 'additional_lysis_buffer_components',
        label: 'Additional lysis buffer components',
        type: 'text',
      },
      {
        key: 'volume_lysis_buffer_components',
        label: 'Volume of lysis buffer components',
        type: 'number',
      },
      { key: 'lysis_incubation_time', label: 'Lysis incubation time', type: 'text' },
      {
        key: 'lysis_incubation_temperature',
        label: 'Lysis incubation temperature',
        type: 'number',
      },
      {
        key: 'volume_of_lysate_used_for_extraction',
        label: 'Volume of lysate used for extraction',
        type: 'number',
      },
      {
        key: 'application_of_further_purification_step',
        label: 'Further purification step applied',
        type: 'boolean',
      },
      {
        key: 'description_of_further_purification_step',
        label: 'Description of further purification step',
        type: 'textarea',
      },
    ],
  },
  {
    key: 'pcr',
    label: 'PCR',
    api: pcrMethodApi,
    laboratoryScoped: true,
    listColumns: ['pcr_kit', 'thermocycler'],
    fields: [
      {
        key: 'pcr_kit_id',
        label: 'PCR kit',
        type: 'category',
        categoryApi: pcrKitApi,
      },
      {
        key: 'thermocycler_id',
        label: 'Thermocycler',
        type: 'category',
        categoryApi: thermocyclerApi,
      },
      { key: 'initial_denaturation_temp', label: 'Initial denaturation temp.', type: 'number' },
      { key: 'initial_denaturation_time', label: 'Initial denaturation time', type: 'text' },
      { key: 'no_of_cycles', label: 'No. of cycles', type: 'number' },
      { key: 'denaturation_temp', label: 'Denaturation temp.', type: 'number' },
      { key: 'denaturation_time', label: 'Denaturation time', type: 'text' },
      { key: 'annealing_temp', label: 'Annealing temp.', type: 'number' },
      { key: 'annealing_time', label: 'Annealing time', type: 'text' },
      { key: 'elongation_temp', label: 'Elongation temp.', type: 'number' },
      { key: 'elongation_time', label: 'Elongation time', type: 'text' },
      { key: 'final_elongation_temp', label: 'Final elongation temp.', type: 'number' },
      { key: 'final_elongation_time', label: 'Final elongation time', type: 'text' },
      { key: 'ramping', label: 'Ramping', type: 'number' },
      { key: 'total_volume_pcr_reaction', label: 'Total volume of PCR reaction', type: 'number' },
    ],
  },
  {
    key: 'ce',
    label: 'CE',
    api: ceMethodApi,
    laboratoryScoped: true,
    listColumns: ['ce_device', 'application_type'],
    fields: [
      {
        key: 'ce_device_id',
        label: 'CE device',
        type: 'category',
        categoryApi: ceDeviceApi,
      },
      { key: 'application_type', label: 'Application type', type: 'text' },
      { key: 'capillary_length', label: 'Capillary length', type: 'number' },
      {
        key: 'polymer_id',
        label: 'Polymer',
        type: 'category',
        categoryApi: polymerApi,
      },
      {
        key: 'dye_set_id',
        label: 'Dye set',
        type: 'category',
        categoryApi: dyeSetApi,
      },
      { key: 'oven_temperature', label: 'Oven temperature', type: 'number' },
      { key: 'run_voltage', label: 'Run voltage', type: 'number' },
      { key: 'pre_run_voltage', label: 'Pre-run voltage', type: 'number' },
      { key: 'injection_voltage', label: 'Injection voltage', type: 'number' },
      { key: 'run_time', label: 'Run time', type: 'text' },
      { key: 'pre_run_time', label: 'Pre-run time', type: 'text' },
      { key: 'injection_time', label: 'Injection time', type: 'text' },
      {
        key: 'type_of_formamide_id',
        label: 'Type of formamide',
        type: 'category',
        categoryApi: typeOfFormamideApi,
      },
      { key: 'volume_formamide', label: 'Volume of formamide', type: 'number' },
      {
        key: 'size_standard_id',
        label: 'Size standard',
        type: 'category',
        categoryApi: sizeStandardApi,
      },
      { key: 'volume_size_standard', label: 'Volume of size standard', type: 'number' },
      { key: 'input_volume_pcr_product', label: 'Input volume PCR product', type: 'number' },
      { key: 'final_volume', label: 'Final volume', type: 'number' },
    ],
  },
  {
    key: 'quantification',
    label: 'Quantification',
    api: quantificationMethodApi,
    laboratoryScoped: true,
    listColumns: ['kit', 'manufacturer'],
    fields: [
      {
        key: 'principle_of_quant_method_category_id',
        label: 'Principle of quantification method',
        type: 'category',
        categoryApi: principleOfQuantMethodCategoryApi,
      },
      {
        key: 'kit_id',
        label: 'Kit',
        type: 'category',
        categoryApi: quantificationKitApi,
      },
      {
        key: 'manufacturer_id',
        label: 'Manufacturer',
        type: 'category',
        categoryApi: manufacturerApi,
      },
      {
        key: 'platform_id',
        label: 'Platform',
        type: 'category',
        categoryApi: platformApi,
      },
      { key: 'description_of_protocol', label: 'Description of protocol', type: 'textarea' },
      {
        key: 'abbreviations_to_manufacturers_protocol',
        label: "Deviations from manufacturer's protocol",
        type: 'textarea',
      },
    ],
  },
  {
    key: 'epg-analysis',
    label: 'EPG Analysis',
    api: epgAnalysisMethodApi,
    laboratoryScoped: true,
    listColumns: ['genotyping_software', 'stutter_filter'],
    fields: [
      {
        key: 'genotyping_software_id',
        label: 'Genotyping software',
        type: 'category',
        categoryApi: genotypingSoftwareApi,
      },
      { key: 'analytical_threshold', label: 'Analytical threshold', type: 'number' },
      {
        key: 'application_analytical_threshold',
        label: 'Application of analytical threshold',
        type: 'text',
      },
      { key: 'stutter_filter', label: 'Stutter filter', type: 'text' },
    ],
  },
  {
    key: 'epg-interpretation',
    label: 'EPG Interpretation',
    api: epgInterpretationMethodApi,
    laboratoryScoped: true,
    listColumns: ['determination_of_noc', 'statistical_software'],
    fields: [
      { key: 'determination_of_noc', label: 'Determination of NOC', type: 'text' },
      {
        key: 'statistical_software_id',
        label: 'Statistical software',
        type: 'category',
        categoryApi: statisticalSoftwareApi,
      },
      {
        key: 'parameters_modelled_by_software',
        label: 'Parameters modelled by software',
        type: 'textarea',
      },
      { key: 'allele_frequency_database', label: 'Allele frequency database', type: 'text' },
    ],
  },
  {
    key: 'post-pcr-treatment',
    label: 'Post-PCR Treatment',
    api: postPcrTreatmentMethodApi,
    laboratoryScoped: true,
    listColumns: ['dilution_of_pcr_product', 'dilution_factor'],
    fields: [
      {
        key: 'application_of_post_pcr_purification_step',
        label: 'Post-PCR purification step applied',
        type: 'boolean',
      },
      {
        key: 'description_of_post_pcr_purification_step',
        label: 'Description of post-PCR purification step',
        type: 'textarea',
      },
      { key: 'dilution_of_pcr_product', label: 'PCR product diluted', type: 'boolean' },
      { key: 'dilution_factor', label: 'Dilution factor', type: 'number' },
    ],
  },
  {
    key: 'swab',
    label: 'Swab',
    api: swabMethodApi,
    laboratoryScoped: false,
    listColumns: ['wetting_agent', 'specification'],
    fields: [
      {
        key: 'type_of_swab_category_id',
        label: 'Type of swab',
        type: 'category',
        categoryApi: typeOfSwabCategoryApi,
      },
      {
        key: 'swabbing_technique_category_id',
        label: 'Swabbing technique',
        type: 'category',
        categoryApi: swabbingTechniqueCategoryApi,
      },
      {
        key: 'wetting_agent_id',
        label: 'Wetting agent',
        type: 'category',
        categoryApi: wettingAgentApi,
      },
      { key: 'volume_of_wetting_agent', label: 'Volume of wetting agent', type: 'number' },
      { key: 'specification', label: 'Specification', type: 'text' },
      { key: 'description', label: 'Description', type: 'textarea' },
    ],
  },
  {
    key: 'tape',
    label: 'Tape',
    api: tapeMethodApi,
    laboratoryScoped: false,
    listColumns: ['supplier'],
    fields: [
      {
        key: 'type_of_tape_id',
        label: 'Type of tape',
        type: 'category',
        categoryApi: typeOfTapeApi,
      },
      { key: 'description', label: 'Description', type: 'textarea' },
      {
        key: 'supplier_id',
        label: 'Supplier',
        type: 'category',
        categoryApi: supplierApi,
      },
    ],
  },
  {
    key: 'vacuum',
    label: 'Vacuum',
    api: vacuumMethodApi,
    laboratoryScoped: false,
    listColumns: ['supplier'],
    fields: [
      {
        key: 'vacuum_device_id',
        label: 'Vacuum device',
        type: 'category',
        categoryApi: vacuumDeviceApi,
      },
      { key: 'description', label: 'Description', type: 'textarea' },
      {
        key: 'supplier_id',
        label: 'Supplier',
        type: 'category',
        categoryApi: supplierApi,
      },
    ],
  },
  {
    key: 'cutting',
    label: 'Cutting',
    api: cuttingMethodApi,
    laboratoryScoped: false,
    listColumns: ['supplier'],
    fields: [
      {
        key: 'cutting_device_id',
        label: 'Cutting device',
        type: 'category',
        categoryApi: cuttingDeviceApi,
      },
      { key: 'description', label: 'Description', type: 'textarea' },
      {
        key: 'supplier_id',
        label: 'Supplier',
        type: 'category',
        categoryApi: supplierApi,
      },
    ],
  },
  {
    key: 'scraping',
    label: 'Scraping',
    api: scrapingMethodApi,
    laboratoryScoped: false,
    listColumns: ['supplier'],
    fields: [
      {
        key: 'scraping_device_id',
        label: 'Scraping device',
        type: 'category',
        categoryApi: scrapingDeviceApi,
      },
      { key: 'description', label: 'Description', type: 'textarea' },
      {
        key: 'supplier_id',
        label: 'Supplier',
        type: 'category',
        categoryApi: supplierApi,
      },
    ],
  },
  {
    key: 'picking',
    label: 'Picking',
    api: pickingMethodApi,
    laboratoryScoped: false,
    listColumns: ['supplier'],
    fields: [
      {
        key: 'picking_device_id',
        label: 'Picking device',
        type: 'category',
        categoryApi: pickingDeviceApi,
      },
      { key: 'description', label: 'Description', type: 'textarea' },
      {
        key: 'supplier_id',
        label: 'Supplier',
        type: 'category',
        categoryApi: supplierApi,
      },
    ],
  },
]

export function getLabMethodConfig(key: string): MethodConfig | undefined {
  return labMethods.find((m) => m.key === key)
}
