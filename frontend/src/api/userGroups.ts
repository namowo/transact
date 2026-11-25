import apiClient from './client'
import type { PermissionInfo, UserGroup, UserGroupPayload } from './types'

export function listPermissions() {
  return apiClient.get<PermissionInfo[]>('/permissions').then((r) => r.data)
}

// Platform-wide groups plus the laboratory groups the user may see. With a
// laboratory, only that laboratory's groups besides the platform-wide ones.
export function listUserGroups(laboratoryId?: string | null) {
  return apiClient
    .get<UserGroup[]>('/user-groups', {
      params: laboratoryId ? { laboratory_id: laboratoryId } : undefined,
    })
    .then((r) => r.data)
}

export function createUserGroup(payload: UserGroupPayload) {
  return apiClient.post<UserGroup>('/user-groups', payload).then((r) => r.data)
}

export function updateUserGroup(id: string, payload: Partial<UserGroupPayload>) {
  return apiClient.patch<UserGroup>(`/user-groups/${id}`, payload).then((r) => r.data)
}

export function deleteUserGroup(id: string) {
  return apiClient.delete(`/user-groups/${id}`)
}
