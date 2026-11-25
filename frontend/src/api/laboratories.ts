import apiClient from './client'
import type { Laboratory, LaboratoryCreate } from './types'

export function listLaboratories() {
  return apiClient.get<Laboratory[]>('/laboratories').then((r) => r.data)
}

export function createLaboratory(payload: LaboratoryCreate) {
  return apiClient.post<Laboratory>('/laboratories', payload).then((r) => r.data)
}

// Changes a laboratory's details (laboratory managers only). Fields sent as
// null are cleared.
export function updateLaboratory(id: string, payload: Partial<LaboratoryCreate>) {
  return apiClient.patch<Laboratory>(`/laboratories/${id}`, payload).then((r) => r.data)
}

// Lets platform admins edit the laboratory's data - or stops them.
export function setAdminDataEntry(id: string, allow: boolean) {
  return apiClient
    .put<Laboratory>(`/laboratories/${id}/data-access`, { allow_admin_data_entry: allow })
    .then((r) => r.data)
}
