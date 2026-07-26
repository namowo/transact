import apiClient from './client'
import type { SurfaceTemplate, SurfaceTemplateInput } from './types'

export function listSurfaceTemplates() {
  return apiClient.get<SurfaceTemplate[]>('/surface-templates').then((r) => r.data)
}

export function getSurfaceTemplate(id: number) {
  return apiClient.get<SurfaceTemplate>(`/surface-templates/${id}`).then((r) => r.data)
}

export function createSurfaceTemplate(payload: SurfaceTemplateInput) {
  return apiClient.post<SurfaceTemplate>('/surface-templates', payload).then((r) => r.data)
}

export function updateSurfaceTemplate(id: number, payload: SurfaceTemplateInput) {
  return apiClient.patch<SurfaceTemplate>(`/surface-templates/${id}`, payload).then((r) => r.data)
}

export function deleteSurfaceTemplate(id: number) {
  return apiClient.delete(`/surface-templates/${id}`)
}
