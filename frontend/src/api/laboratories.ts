import apiClient from './client'
import type { Laboratory, LaboratoryCreate } from './types'

export function listLaboratories() {
  return apiClient.get<Laboratory[]>('/laboratories').then((r) => r.data)
}

export function createLaboratory(payload: LaboratoryCreate) {
  return apiClient.post<Laboratory>('/laboratories', payload).then((r) => r.data)
}
