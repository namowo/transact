import apiClient from './client'
import type {
  CEMethod,
  CEMethodInput,
  CuttingMethod,
  CuttingMethodInput,
  EPGAnalysisMethod,
  EPGAnalysisMethodInput,
  EPGInterpretationMethod,
  EPGInterpretationMethodInput,
  ExtractionMethod,
  ExtractionMethodInput,
  PCRMethod,
  PCRMethodInput,
  PickingMethod,
  PickingMethodInput,
  PostPCRTreatmentMethod,
  PostPCRTreatmentMethodInput,
  QuantificationMethod,
  QuantificationMethodInput,
  Recovery,
  RecoveryInput,
  Result,
  ResultInput,
  SamplingMethod,
  SamplingMethodInput,
  ScrapingMethod,
  ScrapingMethodInput,
  SwabMethod,
  SwabMethodInput,
  TapeMethod,
  TapeMethodInput,
  VacuumMethod,
  VacuumMethodInput,
} from './types'

// All lab-method endpoints share the same REST CRUD shape (list, create,
// update, delete), just under a different URL prefix and payload type.
export function methodApi<TRead, TInput>(basePath: string) {
  return {
    list: () => apiClient.get<TRead[]>(basePath).then((r) => r.data),
    create: (payload: TInput) => apiClient.post<TRead>(basePath, payload).then((r) => r.data),
    update: (id: number, payload: TInput) =>
      apiClient.patch<TRead>(`${basePath}/${id}`, payload).then((r) => r.data),
    delete: (id: number) => apiClient.delete(`${basePath}/${id}`).then(() => undefined),
  }
}

export const extractionMethodApi = methodApi<ExtractionMethod, ExtractionMethodInput>(
  '/extraction-methods',
)
export const pcrMethodApi = methodApi<PCRMethod, PCRMethodInput>('/pcr-methods')
export const ceMethodApi = methodApi<CEMethod, CEMethodInput>('/ce-methods')
export const quantificationMethodApi = methodApi<QuantificationMethod, QuantificationMethodInput>(
  '/quantification-methods',
)
export const epgAnalysisMethodApi = methodApi<EPGAnalysisMethod, EPGAnalysisMethodInput>(
  '/epg-analysis-methods',
)
export const epgInterpretationMethodApi = methodApi<
  EPGInterpretationMethod,
  EPGInterpretationMethodInput
>('/epg-interpretation-methods')
export const postPcrTreatmentMethodApi = methodApi<
  PostPCRTreatmentMethod,
  PostPCRTreatmentMethodInput
>('/post-pcr-treatment-methods')

export const swabMethodApi = methodApi<SwabMethod, SwabMethodInput>('/swab-methods')
export const tapeMethodApi = methodApi<TapeMethod, TapeMethodInput>('/tape-methods')
export const vacuumMethodApi = methodApi<VacuumMethod, VacuumMethodInput>('/vacuum-methods')
export const cuttingMethodApi = methodApi<CuttingMethod, CuttingMethodInput>('/cutting-methods')
export const scrapingMethodApi = methodApi<ScrapingMethod, ScrapingMethodInput>(
  '/scraping-methods',
)
export const pickingMethodApi = methodApi<PickingMethod, PickingMethodInput>('/picking-methods')

export const samplingMethodApi = methodApi<SamplingMethod, SamplingMethodInput>(
  '/sampling-methods',
)

export const recoveryApi = methodApi<Recovery, RecoveryInput>('/recoveries')
export const resultApi = methodApi<Result, ResultInput>('/results')
