import apiClient from './client'
import type { Scenario, ScenarioInput } from './types'

export function listScenarios() {
  return apiClient.get<Scenario[]>('/scenarios').then((r) => r.data)
}

export function getScenario(id: number) {
  return apiClient.get<Scenario>(`/scenarios/${id}`).then((r) => r.data)
}

export function createScenario(payload: ScenarioInput) {
  return apiClient.post<Scenario>('/scenarios', payload).then((r) => r.data)
}

export function updateScenario(id: number, payload: ScenarioInput) {
  return apiClient.patch<Scenario>(`/scenarios/${id}`, payload).then((r) => r.data)
}

export function deleteScenario(id: number) {
  return apiClient.delete(`/scenarios/${id}`)
}
