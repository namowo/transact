import apiClient from './client'
import type {
  JoinExistingLabPayload,
  LabMembershipRequest,
  NewLabRequestPayload,
} from './types'

export function joinExistingLab(payload: JoinExistingLabPayload) {
  return apiClient
    .post<LabMembershipRequest>('/lab-membership-requests/join-existing', payload)
    .then((r) => r.data)
}

export function requestNewLaboratory(payload: NewLabRequestPayload) {
  return apiClient
    .post<LabMembershipRequest>('/lab-membership-requests/new-laboratory', payload)
    .then((r) => r.data)
}

export function fetchMyMembershipRequest() {
  return apiClient
    .get<LabMembershipRequest | null>('/lab-membership-requests/me')
    .then((r) => r.data)
}

export function listPendingForMyLab() {
  return apiClient
    .get<LabMembershipRequest[]>('/lab-membership-requests/pending-for-my-lab')
    .then((r) => r.data)
}

export function listPendingNewLabs() {
  return apiClient
    .get<LabMembershipRequest[]>('/lab-membership-requests/pending-new-labs')
    .then((r) => r.data)
}

export function approveMembershipRequest(id: number) {
  return apiClient
    .post<LabMembershipRequest>(`/lab-membership-requests/${id}/approve`)
    .then((r) => r.data)
}

export function denyMembershipRequest(id: number) {
  return apiClient
    .post<LabMembershipRequest>(`/lab-membership-requests/${id}/deny`)
    .then((r) => r.data)
}
