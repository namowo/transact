import apiClient from './client'
import type { Study, StudyCreate, StudyUpdate } from './types'

export function listStudies() {
  return apiClient.get<Study[]>('/studies').then((r) => r.data)
}

export function getStudy(id: string) {
  return apiClient.get<Study>(`/studies/${id}`).then((r) => r.data)
}

export function createStudy(payload: StudyCreate) {
  return apiClient.post<Study>('/studies', payload).then((r) => r.data)
}

export function updateStudy(id: string, payload: StudyUpdate) {
  return apiClient.patch<Study>(`/studies/${id}`, payload).then((r) => r.data)
}

export function passQualityCheck(id: string) {
  return apiClient.post<Study>(`/studies/${id}/quality-check`).then((r) => r.data)
}

export function deleteStudy(id: string) {
  return apiClient.delete<void>(`/studies/${id}`).then((r) => r.data)
}
