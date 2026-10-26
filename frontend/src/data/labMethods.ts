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
  thermoshakerApi,
  lysisBufferComponentApi,
  ceDeviceApi,
  polymerApi,
  dyeSetApi,
  typeOfFormamideApi,
  sizeStandardApi,
  genotypingSoftwareApi,
  statisticalSoftwareApi,
  quantificationKitApi,
  quantificationPlatformApi,
  platformApi,
  wettingAgentApi,
  supplierApi,
  applicationAnalyticalThresholdApi,
  stutterFilterApi,
  dyeChannelApi,
  modelledParameterApi,
} from '@/api/categories'
import type { NamedCategory, NamedCategoryInput } from '@/api/types'

export type FieldType =
  | 'text'
  | 'textarea'
  | 'number'
  | 'boolean'
  | 'category'
  | 'duration'
  | 'repeatable-group'
  | 'multi-select'
  | 'checkbox-group'
  | 'select'

export interface MethodFieldConfig {
  key: string
  label: string
  type: FieldType
  // For 'category' fields: the dropdown's data source + create endpoint.
  categoryApi?: {
    list: () => Promise<NamedCategory[]>
    create: (payload: NamedCategoryInput) => Promise<NamedCategory>
  }
  // For 'number' fields: unit shown as a badge next to the input (e.g. "µl", "°C").
  unit?: string
  // For 'number' fields: increment step, also controls decimal precision
  // (e.g. 0.1 allows one decimal place). Defaults to 1 (integers only).
  step?: number
  // For 'duration' fields: which unit inputs to show (defaults to all, from
  // seconds to years). Restrict this for durations that never need more than
  // e.g. hours/minutes.
  durationUnits?: Array<'years' | 'days' | 'hours' | 'minutes' | 'seconds'>
  // For 'repeatable-group' fields: the row shape - each row has its own
  // (non-repeatable) fields, e.g. a component dropdown + a volume number.
  rowFields?: MethodFieldConfig[]
  // For 'repeatable-group' fields: label for the "add row" button.
  addRowLabel?: string
  // For 'select' fields: the fixed list of choices.
  options?: Array<{ label: string; value: string }>
  // Explanatory text shown next to the field label (e.g. unit conversion hints).
  hint?: string
  // When set, the field is only rendered while this returns true for the
  // form's current values (e.g. a "describe further" field that only makes
  // sense once its related toggle is on).
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- form values are dynamic per method config
  visibleWhen?: (values: Record<string, any>) => boolean
  // For 'number' fields: derives the field's value from other field values
  // instead of letting the user type it directly (e.g. a volume that's the
  // sum of other volumes, kept as a stored "double check" value rather than
  // purely cosmetic). The input is shown disabled/read-only.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- form values are dynamic per method config
  computed?: (values: Record<string, any>) => number | null
  // For 'multi-select' fields: the API returns the selection as a list of
  // objects under a different key (e.g. `modelled_parameters`) than the
  // `..._ids` field the form submits - this says which key to read ids
  // from when hydrating the form from an existing record.
  sourceKey?: string
  // Column shown in the list table for this field (defaults to true for the
  // first few fields via `listColumns` below, not per-field).
}

export interface MethodConfig {
  key: string
  label: string
  // Phrase used for the "Add ... entry" button and modal title, when it
  // shouldn't just be `label` lowercased (e.g. "STR-PCR method" instead of
  // "pcr entry").
  entryLabel?: string
  api: {
    list: () => Promise<any[]>
    create: (payload: any) => Promise<any>
    update: (id: string, payload: any) => Promise<any>
    delete: (id: string) => Promise<void>
  }
  laboratoryScoped: boolean
  fields: MethodFieldConfig[]
  // Which field keys to show as DataTable columns (besides id).
  listColumns: string[]
  // Header labels for list columns that aren't editable in the form (so
  // they have no entry in `fields` to derive a label from) - e.g. a value
  // shown for reference only.
  listColumnLabels?: Record<string, string>
}

export const labMethods: MethodConfig[] = [
  {
    key: 'extraction',
    label: 'Extraction',
    entryLabel: 'extraction method',
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
        key: 'lysis_buffer_components',
        label: 'Lysis buffer components',
        type: 'repeatable-group',
        addRowLabel: 'Add component',
        rowFields: [
          {
            key: 'lysis_buffer_component_id',
            label: 'Component',
            type: 'category',
            categoryApi: lysisBufferComponentApi,
          },
          { key: 'volume', label: 'Volume', type: 'number', unit: 'µl' },
        ],
      },
      {
        key: 'lysis_incubation_time',
        label: 'Lysis incubation time',
        type: 'duration',
        durationUnits: ['hours', 'minutes'],
      },
      {
        key: 'lysis_incubation_temperature',
        label: 'Lysis incubation temperature',
        type: 'number',
        unit: '°C',
      },
      {
        key: 'thermoshaker_id',
        label: 'Thermoshaker',
        type: 'category',
        categoryApi: thermoshakerApi,
      },
      {
        key: 'rcf',
        label: 'RCF',
        type: 'number',
        unit: 'x g',
        hint: 'As RPM is device-specific, please convert to RCF using the formula RCF = 1.118 × 10⁻⁵ × r × RPM².',
      },
      {
        key: 'volume_of_lysate_used_for_extraction',
        label: 'Volume of lysate used for extraction',
        type: 'number',
        unit: 'µl',
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
        visibleWhen: (values) => values.application_of_further_purification_step === true,
      },
      {
        key: 'abbreviations_to_manufacturers_protocol',
        label: "Deviations from manufacturer's protocol",
        type: 'textarea',
      },
    ],
  },
  {
    key: 'pcr',
    label: 'PCR',
    entryLabel: 'STR-PCR method',
    api: pcrMethodApi,
    laboratoryScoped: true,
    // Kit + thermocycler alone don't distinguish entries that only differ by
    // cycle count, so surface it as a third column.
    listColumns: ['pcr_kit', 'thermocycler', 'no_of_cycles'],
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
      {
        key: 'initial_denaturation_temp',
        label: 'Initial denaturation temp.',
        type: 'number',
        unit: '°C',
      },
      { key: 'initial_denaturation_time', label: 'Initial denaturation time', type: 'duration' },
      { key: 'no_of_cycles', label: 'No. of cycles', type: 'number' },
      { key: 'denaturation_temp', label: 'Denaturation temp.', type: 'number', unit: '°C' },
      { key: 'denaturation_time', label: 'Denaturation time', type: 'duration' },
      { key: 'annealing_temp', label: 'Annealing temp.', type: 'number', unit: '°C' },
      { key: 'annealing_time', label: 'Annealing time', type: 'duration' },
      { key: 'elongation_temp', label: 'Elongation temp.', type: 'number', unit: '°C' },
      { key: 'elongation_time', label: 'Elongation time', type: 'duration' },
      {
        key: 'final_elongation_temp',
        label: 'Final elongation temp.',
        type: 'number',
        unit: '°C',
      },
      { key: 'final_elongation_time', label: 'Final elongation time', type: 'duration' },
      { key: 'ramping', label: 'Ramping', type: 'number', unit: '°C/s' },
      {
        key: 'total_volume_pcr_reaction',
        label: 'Total volume of PCR reaction',
        type: 'number',
        unit: 'µl',
        step: 0.1,
      },
      {
        key: 'abbreviations_to_manufacturers_protocol',
        label: "Deviations from manufacturer's protocol",
        type: 'textarea',
      },
    ],
  },
  {
    key: 'ce',
    label: 'CE',
    entryLabel: 'CE method',
    api: ceMethodApi,
    laboratoryScoped: true,
    listColumns: ['ce_device', 'dye_set'],
    // Dye set depends on the PCR kit used and isn't editable here (see the
    // field list below), but it's still shown for reference.
    listColumnLabels: { dye_set: 'Dye set' },
    fields: [
      {
        key: 'ce_device_id',
        label: 'CE device',
        type: 'category',
        categoryApi: ceDeviceApi,
      },
      { key: 'capillary_length', label: 'Capillary length', type: 'number', unit: 'cm' },
      {
        key: 'polymer_id',
        label: 'Polymer',
        type: 'category',
        categoryApi: polymerApi,
      },
      { key: 'oven_temperature', label: 'Oven temperature', type: 'number', unit: '°C' },
      { key: 'run_voltage', label: 'Run voltage', type: 'number', unit: 'V' },
      { key: 'pre_run_voltage', label: 'Pre-run voltage', type: 'number', unit: 'V' },
      { key: 'injection_voltage', label: 'Injection voltage', type: 'number', unit: 'V' },
      { key: 'run_time', label: 'Run time', type: 'duration' },
      { key: 'pre_run_time', label: 'Pre-run time', type: 'duration' },
      { key: 'injection_time', label: 'Injection time', type: 'duration' },
      {
        key: 'type_of_formamide_id',
        label: 'Type of formamide',
        type: 'category',
        categoryApi: typeOfFormamideApi,
      },
      {
        key: 'volume_formamide',
        label: 'Volume of formamide',
        type: 'number',
        unit: 'µl',
        step: 0.1,
      },
      {
        key: 'size_standard_id',
        label: 'Size standard',
        type: 'category',
        categoryApi: sizeStandardApi,
      },
      {
        key: 'volume_size_standard',
        label: 'Volume of size standard',
        type: 'number',
        unit: 'µl',
      },
      {
        key: 'input_volume_pcr_product',
        label: 'Input volume PCR product',
        type: 'number',
        unit: 'µl',
        step: 0.1,
      },
      {
        key: 'final_volume',
        label: 'Final volume',
        type: 'number',
        unit: 'µl',
        hint: 'Calculated automatically as formamide + size standard + PCR product, for a double check against what was actually measured.',
        computed: (values) =>
          [values.volume_formamide, values.volume_size_standard, values.input_volume_pcr_product].every(
            (v) => v !== null && v !== undefined && v !== '',
          )
            ? Number(values.volume_formamide) +
              Number(values.volume_size_standard) +
              Number(values.input_volume_pcr_product)
            : null,
      },
    ],
  },
  {
    key: 'quantification',
    label: 'Quantification',
    entryLabel: 'quantification method',
    api: quantificationMethodApi,
    laboratoryScoped: true,
    listColumns: ['kit', 'platform'],
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
        key: 'platform_id',
        label: 'Platform',
        type: 'category',
        categoryApi: quantificationPlatformApi,
      },
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
    entryLabel: 'EPG analysis method',
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
      {
        key: 'pcr_kit_id',
        label: 'PCR kit',
        type: 'category',
        categoryApi: pcrKitApi,
        hint: 'The number of dye channels available below depends on the kit used.',
      },
      {
        key: 'dye_channel_thresholds',
        label: 'Analytical threshold by dye channel',
        type: 'repeatable-group',
        addRowLabel: 'Add channel',
        rowFields: [
          {
            key: 'dye_channel_id',
            label: 'Dye channel',
            type: 'category',
            categoryApi: dyeChannelApi,
          },
          { key: 'analytical_threshold', label: 'Threshold', type: 'number', unit: 'RFU' },
        ],
      },
      {
        key: 'application_analytical_threshold',
        label: 'Application of analytical threshold',
        type: 'text',
      },
      {
        key: 'stutter_filter_id',
        label: 'Stutter filter',
        type: 'category',
        categoryApi: stutterFilterApi,
      },
      { key: 'description', label: 'Description', type: 'textarea' },
    ],
  },
  {
    key: 'epg-interpretation',
    label: 'EPG Interpretation',
    entryLabel: 'EPG interpretation method',
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
        key: 'modelled_parameter_ids',
        label: 'Parameters modelled by software',
        type: 'checkbox-group',
        categoryApi: modelledParameterApi,
        sourceKey: 'modelled_parameters',
      },
      { key: 'allele_frequency_database', label: 'Allele frequency database', type: 'text' },
      {
        key: 'application_analytical_threshold_id',
        label: 'Application of analytical threshold',
        type: 'category',
        categoryApi: applicationAnalyticalThresholdApi,
      },
      {
        key: 'stutter_filter_id',
        label: 'Stutter filter',
        type: 'category',
        categoryApi: stutterFilterApi,
      },
      { key: 'description', label: 'Description', type: 'textarea' },
    ],
  },
  {
    key: 'post-pcr-treatment',
    label: 'Post-PCR Treatment',
    entryLabel: 'post-PCR treatment method',
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
    entryLabel: 'swab method',
    api: swabMethodApi,
    laboratoryScoped: false,
    listColumns: ['wetting_agent'],
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
      {
        key: 'volume_of_wetting_agent',
        label: 'Volume of wetting agent',
        type: 'number',
        unit: 'µl',
      },
      {
        key: 'volume_of_wetting_agent_type',
        label: 'Volume of wetting agent is',
        type: 'select',
        options: [
          { label: 'Approximate', value: 'approximate' },
          { label: 'Measured', value: 'measured' },
        ],
      },
      { key: 'description', label: 'Description', type: 'textarea' },
    ],
  },
  {
    key: 'tape',
    label: 'Tape',
    entryLabel: 'tape method',
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
    entryLabel: 'vacuum method',
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
    entryLabel: 'cutting method',
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
    entryLabel: 'scraping method',
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
    entryLabel: 'picking method',
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
