import apiClient from './client'
import type { User } from './types'

export interface UpdateProfilePayload {
  first_name?: string
  last_name?: string
  laboratory_id?: number
}

export function updateMe(payload: UpdateProfilePayload) {
  return apiClient.patch<User>('/users/me', payload).then((r) => r.data)
}
