import apiClient from './client'
import type { SortableTable, TableSortMeta, User } from './types'
import type { TourId } from '@/tours/types'

export interface UpdateProfilePayload {
  first_name?: string
  last_name?: string
  locale?: string
  table_sorts?: Partial<Record<SortableTable, TableSortMeta[]>>
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

// Remembers that the user finished or skipped an interactive guide.
export function completeTour(tour: TourId) {
  return apiClient.post<User>(`/users/me/completed-tours/${tour}`).then((r) => r.data)
}

// Replaces the user's groups; the backend checks each group that changes.
export function setUserGroups(id: string, groupIds: string[]) {
  return apiClient
    .put<User>(`/users/${id}/groups`, { group_ids: groupIds })
    .then((r) => r.data)
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
