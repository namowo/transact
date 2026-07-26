import apiClient from './client'
import type { Surface, SurfaceInput } from './types'

export function listSurfaces() {
  return apiClient.get<Surface[]>('/surfaces').then((r) => r.data)
}

export function getSurface(id: number) {
  return apiClient.get<Surface>(`/surfaces/${id}`).then((r) => r.data)
}

export function createSurface(payload: SurfaceInput) {
  return apiClient.post<Surface>('/surfaces', payload).then((r) => r.data)
}

export function updateSurface(id: number, payload: SurfaceInput) {
  return apiClient.patch<Surface>(`/surfaces/${id}`, payload).then((r) => r.data)
}

export function deleteSurface(id: number) {
  return apiClient.delete(`/surfaces/${id}`)
}
