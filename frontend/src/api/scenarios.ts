import apiClient from './client'
import type { Scenario, ScenarioInput } from './types'

// With a study, only the scenarios linked to that study.
export function listScenarios(studyId?: string) {
  return apiClient
    .get<Scenario[]>('/scenarios', { params: studyId ? { study_id: studyId } : {} })
    .then((r) => r.data)
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
