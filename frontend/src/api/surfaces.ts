import apiClient from './client'
import type { Surface, SurfaceInput } from './types'

export function createSurface(payload: SurfaceInput) {
  return apiClient.post<Surface>('/surfaces', payload).then((r) => r.data)
}

export function updateSurface(id: number, payload: SurfaceInput) {
  return apiClient.patch<Surface>(`/surfaces/${id}`, payload).then((r) => r.data)
}
