import apiClient from './client'
import type { User } from './types'

export interface UpdateProfilePayload {
  first_name?: string
  last_name?: string
  laboratory_id?: string
}

export function updateMe(payload: UpdateProfilePayload) {
  return apiClient.patch<User>('/users/me', payload).then((r) => r.data)
}

export interface ChangePasswordPayload {
  current_password: string
  new_password: string
}

export function changePassword(payload: ChangePasswordPayload) {
  return apiClient.post<User>('/users/me/change-password', payload).then((r) => r.data)
}

export interface ChangeEmailPayload {
  current_password: string
  new_email: string
}

export function changeEmail(payload: ChangeEmailPayload) {
  return apiClient.post<User>('/users/me/change-email', payload).then((r) => r.data)
}

export function dismissPasskeyPrompt() {
  return apiClient.post<User>('/users/me/dismiss-passkey-prompt').then((r) => r.data)
}

export function grantQualityCheck(id: string) {
  return apiClient.post<User>(`/users/${id}/grant-quality-check`).then((r) => r.data)
}

export function revokeQualityCheck(id: string) {
  return apiClient.post<User>(`/users/${id}/revoke-quality-check`).then((r) => r.data)
}

export function grantLabAdmin(id: string) {
  return apiClient.post<User>(`/users/${id}/grant-lab-admin`).then((r) => r.data)
}

export function revokeLabAdmin(id: string) {
  return apiClient.post<User>(`/users/${id}/revoke-lab-admin`).then((r) => r.data)
}

export function grantSuperuser(id: string) {
  return apiClient.post<User>(`/users/${id}/grant-superuser`).then((r) => r.data)
}

export function revokeSuperuser(id: string) {
  return apiClient.post<User>(`/users/${id}/revoke-superuser`).then((r) => r.data)
}

export function removeFromLaboratory(id: string) {
  return apiClient.post<User>(`/users/${id}/remove-from-laboratory`).then((r) => r.data)
}

export function setLaboratory(id: string, laboratoryId: string | null) {
  return apiClient
    .post<User>(`/users/${id}/set-laboratory`, { laboratory_id: laboratoryId })
    .then((r) => r.data)
}

export function deleteUser(id: string) {
  return apiClient.delete(`/users/${id}`)
}

export function listLabUsers(laboratoryId: string) {
  return apiClient
    .get<User[]>(`/laboratories/${laboratoryId}/users`)
    .then((r) => r.data)
}

export function listAllUsers() {
  return apiClient.get<User[]>('/users').then((r) => r.data)
}
