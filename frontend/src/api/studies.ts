import apiClient from './client'
import type { Study, StudyCreate, StudyUpdate } from './types'

export function listStudies() {
  return apiClient.get<Study[]>('/studies').then((r) => r.data)
}

export function getStudy(id: number) {
  return apiClient.get<Study>(`/studies/${id}`).then((r) => r.data)
}

export function createStudy(payload: StudyCreate) {
  return apiClient.post<Study>('/studies', payload).then((r) => r.data)
}

export function updateStudy(id: number, payload: StudyUpdate) {
  return apiClient.patch<Study>(`/studies/${id}`, payload).then((r) => r.data)
}

export function passQualityCheck(id: number) {
  return apiClient.post<Study>(`/studies/${id}/quality-check`).then((r) => r.data)
}
