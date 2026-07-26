import apiClient from './client'
import type {
  NamedCategory,
  NamedCategoryInput,
  SkinDiseaseCategory,
  SkinDiseaseCategoryInput,
  DeterminationOfSheddingPropensityCategory,
  DeterminationOfSheddingPropensityCategoryInput,
  Supplier,
  SupplierInput,
} from './types'

// Every "simple" lookup category (disturbance, surface material, body part
// condition, ...) shares the same { id, name, description } shape and CRUD
// routes, just under a different URL prefix. Rather than hand-writing one
// api module per category, build the handful of functions once per prefix.
export function namedCategoryApi(basePath: string) {
  return {
    list: () => apiClient.get<NamedCategory[]>(basePath).then((r) => r.data),
    create: (payload: NamedCategoryInput) =>
      apiClient.post<NamedCategory>(basePath, payload).then((r) => r.data),
  }
}

export const activityCategoryApi = namedCategoryApi('/activity-categories')
export const bodyPartConditionCategoryApi = namedCategoryApi('/body-part-condition-categories')
export const conditionOfItemPartCategoryApi = namedCategoryApi('/condition-of-item-part-categories')
export const disturbanceCategoryApi = namedCategoryApi('/disturbance-categories')
export const geographicLocationCategoryApi = namedCategoryApi('/geographic-location-categories')
export const itemCategoryApi = namedCategoryApi('/item-categories')
export const itemPartsCategoryApi = namedCategoryApi('/item-parts-categories')
export const itemSubcategoryApi = namedCategoryApi('/item-subcategories')
export const locationOfBodyCategoryApi = namedCategoryApi('/location-of-body-categories')
export const scenarioCategoryApi = namedCategoryApi('/scenario-categories')
export const sexApi = namedCategoryApi('/sexes')
export const dnaSheddingPropensityCategoryApi = namedCategoryApi(
  '/dna-shedding-propensity-categories',
)
export const sourceOfDnaCategoryApi = namedCategoryApi('/source-of-dna-categories')
export const surfaceMaterialCategoryApi = namedCategoryApi('/surface-material-categories')
export const pressureEstimateApi = namedCategoryApi('/pressure-estimates')
export const experienceLevelCategoryApi = namedCategoryApi('/experience-levels')
export const frictionAppliedEstimateApi = namedCategoryApi('/friction-applied-estimates')
export const principleOfExtractionMethodCategoryApi = namedCategoryApi(
  '/principle-of-extraction-method-categories',
)
export const principleOfQuantMethodCategoryApi = namedCategoryApi(
  '/principle-of-quant-method-categories',
)
export const typeOfSwabCategoryApi = namedCategoryApi('/type-of-swab-categories')
export const swabbingTechniqueCategoryApi = namedCategoryApi('/swabbing-technique-categories')
export const typeOfTapeApi = namedCategoryApi('/type-of-tape')
export const cuttingDeviceApi = namedCategoryApi('/cutting-devices')
export const vacuumDeviceApi = namedCategoryApi('/vacuum-devices')
export const scrapingDeviceApi = namedCategoryApi('/scraping-devices')
export const pickingDeviceApi = namedCategoryApi('/picking-devices')

// Equipment / reagents / software referenced from the lab Methods
export const pcrKitApi = namedCategoryApi('/pcr-kits')
export const thermocyclerApi = namedCategoryApi('/thermocyclers')
export const ceDeviceApi = namedCategoryApi('/ce-devices')
export const polymerApi = namedCategoryApi('/polymers')
export const dyeSetApi = namedCategoryApi('/dye-sets')
export const typeOfFormamideApi = namedCategoryApi('/types-of-formamide')
export const sizeStandardApi = namedCategoryApi('/size-standards')
export const genotypingSoftwareApi = namedCategoryApi('/genotyping-software')
export const statisticalSoftwareApi = namedCategoryApi('/statistical-software')
export const quantificationKitApi = namedCategoryApi('/quantification-kits')
export const manufacturerApi = namedCategoryApi('/manufacturers')
export const platformApi = namedCategoryApi('/platforms')
export const wettingAgentApi = namedCategoryApi('/wetting-agents')

export const skinDiseaseCategoryApi = {
  list: () => apiClient.get<SkinDiseaseCategory[]>('/skin-disease-categories').then((r) => r.data),
  create: (payload: SkinDiseaseCategoryInput) =>
    apiClient.post<SkinDiseaseCategory>('/skin-disease-categories', payload).then((r) => r.data),
}

export const determinationOfSheddingPropensityCategoryApi = {
  list: () =>
    apiClient
      .get<DeterminationOfSheddingPropensityCategory[]>(
        '/determination-of-shedding-propensity-categories',
      )
      .then((r) => r.data),
  create: (payload: DeterminationOfSheddingPropensityCategoryInput) =>
    apiClient
      .post<DeterminationOfSheddingPropensityCategory>(
        '/determination-of-shedding-propensity-categories',
        payload,
      )
      .then((r) => r.data),
}

export const supplierApi = {
  list: () => apiClient.get<Supplier[]>('/suppliers').then((r) => r.data),
  create: (payload: SupplierInput) =>
    apiClient.post<Supplier>('/suppliers', payload).then((r) => r.data),
}
