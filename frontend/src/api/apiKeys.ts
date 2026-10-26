import apiClient from './client'
import type { ApiKey, ApiKeyCreated, ApiKeyCreatePayload } from './types'

export function listApiKeys() {
  return apiClient.get<ApiKey[]>('/auth/api-keys').then((r) => r.data)
}

export function createApiKey(payload: ApiKeyCreatePayload) {
  return apiClient.post<ApiKeyCreated>('/auth/api-keys', payload).then((r) => r.data)
}

export function revokeApiKey(id: string) {
  return apiClient.delete(`/auth/api-keys/${id}`).then(() => undefined)
}
