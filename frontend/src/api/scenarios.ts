import apiClient from './client'
import type { Scenario, ScenarioInput } from './types'

export function listScenarios() {
  return apiClient.get<Scenario[]>('/scenarios').then((r) => r.data)
}

export function getScenario(id: string) {
  return apiClient.get<Scenario>(`/scenarios/${id}`).then((r) => r.data)
}

export function createScenario(payload: ScenarioInput) {
  return apiClient.post<Scenario>('/scenarios', payload).then((r) => r.data)
}

export function updateScenario(id: string, payload: ScenarioInput) {
  return apiClient.patch<Scenario>(`/scenarios/${id}`, payload).then((r) => r.data)
}

export function deleteScenario(id: string) {
  return apiClient.delete(`/scenarios/${id}`)
}
