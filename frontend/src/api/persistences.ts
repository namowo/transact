import apiClient from './client'
import type { Persistence, PersistenceInput } from './types'

export function createPersistence(payload: PersistenceInput) {
  return apiClient.post<Persistence>('/persistences', payload).then((r) => r.data)
}

export function updatePersistence(id: number, payload: PersistenceInput) {
  return apiClient.patch<Persistence>(`/persistences/${id}`, payload).then((r) => r.data)
}
