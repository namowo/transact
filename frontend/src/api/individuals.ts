import apiClient from './client'
import type { Individual, IndividualInput } from './types'

export function listIndividuals() {
  return apiClient.get<Individual[]>('/individuals').then((r) => r.data)
}

export function createIndividual(payload: IndividualInput) {
  return apiClient.post<Individual>('/individuals', payload).then((r) => r.data)
}

export function updateIndividual(id: number, payload: IndividualInput) {
  return apiClient.patch<Individual>(`/individuals/${id}`, payload).then((r) => r.data)
}
