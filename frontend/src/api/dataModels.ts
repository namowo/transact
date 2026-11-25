import apiClient from './client'
import { filenameFrom, saveBlob, unwrapBlobError } from './download'
import type {
  Catalog,
  DataModel,
  DataModelDefinition,
  DataModelPreview,
  DataModelSave,
  DownloadableStudy,
  ExportFormat,
} from './types'

let catalogRequest: Promise<Catalog> | null = null

// The catalog only changes with a deploy, so it's fetched once per page load.
export function getCatalog() {
  catalogRequest ??= apiClient
    .get<Catalog>('/data-models/catalog')
    .then((r) => r.data)
    .catch((err) => {
      catalogRequest = null
      throw err
    })
  return catalogRequest
}

export function getFieldValues(dataset: string, field: string) {
  return apiClient
    .get<(string | number | boolean)[]>(
      `/data-models/catalog/${encodeURIComponent(dataset)}/fields/${encodeURIComponent(field)}/values`,
    )
    .then((r) => r.data)
}

export function listDownloadableStudies() {
  return apiClient.get<DownloadableStudy[]>('/data-models/studies').then((r) => r.data)
}

export function listDataModels() {
  return apiClient.get<DataModel[]>('/data-models').then((r) => r.data)
}

export function getDataModel(id: string) {
  return apiClient.get<DataModel>(`/data-models/${id}`).then((r) => r.data)
}

export function createDataModel(payload: DataModelSave) {
  return apiClient.post<DataModel>('/data-models', payload).then((r) => r.data)
}

export function updateDataModel(id: string, payload: Partial<DataModelSave>) {
  return apiClient.patch<DataModel>(`/data-models/${id}`, payload).then((r) => r.data)
}

export function deleteDataModel(id: string) {
  return apiClient.delete<void>(`/data-models/${id}`).then((r) => r.data)
}

export function previewDataModel(definition: DataModelDefinition, signal?: AbortSignal) {
  return apiClient
    .post<DataModelPreview>('/data-models/preview', definition, { signal })
    .then((r) => r.data)
}

/** Download an unsaved definition. */
export async function downloadDefinition(
  definition: DataModelDefinition,
  format: ExportFormat,
  name: string,
) {
  const response = await apiClient
    .post<Blob>('/data-models/download', definition, {
      params: { format, name },
      responseType: 'blob',
    })
    .catch(unwrapBlobError)
  saveBlob(
    response.data,
    filenameFrom(response.headers['content-disposition'], `transact-data.${format}`),
  )
}

/** Download a saved or predefined model with the latest data. */
export async function downloadDataModel(id: string, format: ExportFormat) {
  const response = await apiClient
    .get<Blob>(`/data-models/${id}/download`, { params: { format }, responseType: 'blob' })
    .catch(unwrapBlobError)
  saveBlob(
    response.data,
    filenameFrom(response.headers['content-disposition'], `transact-data.${format}`),
  )
}

/** The URL scripts can fetch a saved model from, with an API key. */
export function dataModelDownloadUrl(id: string, format: ExportFormat = 'csv') {
  const base = apiClient.defaults.baseURL ?? '/api/v1'
  const absolute = new URL(base, window.location.origin).toString().replace(/\/$/, '')
  return `${absolute}/data-models/${id}/download?format=${format}`
}
