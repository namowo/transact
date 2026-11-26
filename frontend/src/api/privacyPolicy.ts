import apiClient from './client'
import type {
  PrivacyPolicy,
  PrivacyPolicyAdmin,
  PrivacyPolicyDraftInput,
  User,
} from './types'

export const privacyPolicyApi = {
  // The policy in force, or null if none was published yet.
  getActive: () => apiClient.get<PrivacyPolicy | null>('/privacy-policy').then((r) => r.data),
  get: (id: number) =>
    apiClient.get<PrivacyPolicy>(`/privacy-policy/versions/${id}`).then((r) => r.data),
  list: () =>
    apiClient.get<PrivacyPolicyAdmin[]>('/privacy-policy/versions').then((r) => r.data),
  createDraft: (payload: PrivacyPolicyDraftInput = {}) =>
    apiClient.post<PrivacyPolicyAdmin>('/privacy-policy/versions', payload).then((r) => r.data),
  updateDraft: (id: number, payload: PrivacyPolicyDraftInput) =>
    apiClient
      .patch<PrivacyPolicyAdmin>(`/privacy-policy/versions/${id}`, payload)
      .then((r) => r.data),
  discardDraft: (id: number) => apiClient.delete(`/privacy-policy/versions/${id}`),
  publish: (id: number, notifyUsers: boolean) =>
    apiClient
      .post<PrivacyPolicyAdmin>(`/privacy-policy/versions/${id}/publish`, {
        notify_users: notifyUsers,
      })
      .then((r) => r.data),
  accept: (privacyPolicyId: number) =>
    apiClient
      .post<User>('/privacy-policy/consent', { privacy_policy_id: privacyPolicyId })
      .then((r) => r.data),
}
