import apiClient from './client'
import type {
  NamedCategory,
  NamedCategoryInput,
  SkinDiseaseCategory,
  SkinDiseaseCategoryInput,
  DeterminationOfSheddingPropensityCategory,
  DeterminationOfSheddingPropensityCategoryInput,
  ItemSubcategory,
  ItemSubcategoryInput,
  ItemPartsCategory,
  ItemPartsCategoryInput,
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
    update: (id: string, payload: NamedCategoryInput) =>
      apiClient.patch<NamedCategory>(`${basePath}/${id}`, payload).then((r) => r.data),
  }
}

export const activityCategoryApi = namedCategoryApi('/activity-categories')
export const bodyPartConditionCategoryApi = namedCategoryApi('/body-part-condition-categories')
export const conditionOfItemPartCategoryApi = namedCategoryApi('/condition-of-item-part-categories')
export const disturbanceCategoryApi = namedCategoryApi('/disturbance-categories')
export const geographicLocationCategoryApi = namedCategoryApi('/geographic-location-categories')
export const degradationCategoryApi = namedCategoryApi('/degradation-categories')
export const inhibitionCategoryApi = namedCategoryApi('/inhibition-categories')

// Not a plain namedCategoryApi: the admin item catalog screen needs to
// rename/delete categories, so this exposes update/delete too.
export const itemCategoryApi = {
  list: () => apiClient.get<NamedCategory[]>('/item-categories').then((r) => r.data),
  create: (payload: NamedCategoryInput) =>
    apiClient.post<NamedCategory>('/item-categories', payload).then((r) => r.data),
  update: (id: string, payload: NamedCategoryInput) =>
    apiClient.patch<NamedCategory>(`/item-categories/${id}`, payload).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/item-categories/${id}`).then(() => undefined),
}

// Not a plain namedCategoryApi: a subcategory belongs to one item category,
// so callers need item_category_id both when listing (to filter client-side)
// and when creating (to attach the new subcategory to the right category).
// update/delete are needed by the admin item catalog screen.
export const itemSubcategoryApi = {
  list: () => apiClient.get<ItemSubcategory[]>('/item-subcategories').then((r) => r.data),
  create: (payload: ItemSubcategoryInput) =>
    apiClient.post<ItemSubcategory>('/item-subcategories', payload).then((r) => r.data),
  update: (id: string, payload: ItemSubcategoryInput) =>
    apiClient.patch<ItemSubcategory>(`/item-subcategories/${id}`, payload).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/item-subcategories/${id}`).then(() => undefined),
}

// Likewise category-scoped: an item part belongs to one item category, and
// the inline rename dialog (ItemPartSelect) plus the admin item catalog
// screen both need update/delete.
export const itemPartsCategoryApi = {
  list: () => apiClient.get<ItemPartsCategory[]>('/item-parts-categories').then((r) => r.data),
  create: (payload: ItemPartsCategoryInput) =>
    apiClient.post<ItemPartsCategory>('/item-parts-categories', payload).then((r) => r.data),
  update: (id: string, payload: ItemPartsCategoryInput) =>
    apiClient.patch<ItemPartsCategory>(`/item-parts-categories/${id}`, payload).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/item-parts-categories/${id}`).then(() => undefined),
}

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
export const thermoshakerApi = namedCategoryApi('/thermoshakers')
export const lysisBufferComponentApi = namedCategoryApi('/lysis-buffer-components')
export const ceDeviceApi = namedCategoryApi('/ce-devices')
export const polymerApi = namedCategoryApi('/polymers')
export const dyeSetApi = namedCategoryApi('/dye-sets')
export const typeOfFormamideApi = namedCategoryApi('/types-of-formamide')
export const sizeStandardApi = namedCategoryApi('/size-standards')
export const genotypingSoftwareApi = namedCategoryApi('/genotyping-software')
export const statisticalSoftwareApi = namedCategoryApi('/statistical-software')
export const quantificationKitApi = namedCategoryApi('/quantification-kits')
export const quantificationPlatformApi = namedCategoryApi('/quantification-platforms')
export const manufacturerApi = namedCategoryApi('/manufacturers')
export const platformApi = namedCategoryApi('/platforms')
export const wettingAgentApi = namedCategoryApi('/wetting-agents')
export const applicationAnalyticalThresholdApi = namedCategoryApi(
  '/application-analytical-thresholds',
)
export const stutterFilterApi = namedCategoryApi('/stutter-filters')
export const dyeChannelApi = namedCategoryApi('/dye-channels')
export const modelledParameterApi = namedCategoryApi('/modelled-parameters')

export const skinDiseaseCategoryApi = {
  list: () => apiClient.get<SkinDiseaseCategory[]>('/skin-disease-categories').then((r) => r.data),
  create: (payload: SkinDiseaseCategoryInput) =>
    apiClient.post<SkinDiseaseCategory>('/skin-disease-categories', payload).then((r) => r.data),
  update: (id: string, payload: SkinDiseaseCategoryInput) =>
    apiClient
      .patch<SkinDiseaseCategory>(`/skin-disease-categories/${id}`, payload)
      .then((r) => r.data),
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
  update: (id: string, payload: DeterminationOfSheddingPropensityCategoryInput) =>
    apiClient
      .patch<DeterminationOfSheddingPropensityCategory>(
        `/determination-of-shedding-propensity-categories/${id}`,
        payload,
      )
      .then((r) => r.data),
}

export const supplierApi = {
  list: () => apiClient.get<Supplier[]>('/suppliers').then((r) => r.data),
  create: (payload: SupplierInput) =>
    apiClient.post<Supplier>('/suppliers', payload).then((r) => r.data),
  update: (id: string, payload: SupplierInput) =>
    apiClient.patch<Supplier>(`/suppliers/${id}`, payload).then((r) => r.data),
}
