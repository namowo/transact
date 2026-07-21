import apiClient from './client'
import type { User, WebAuthnCredential } from './types'

export function getRegistrationOptions() {
  return apiClient.post('/auth/webauthn/register/options').then((r) => r.data)
}

export function verifyRegistration(credential: unknown, deviceName?: string) {
  return apiClient
    .post<WebAuthnCredential>('/auth/webauthn/register/verify', {
      credential,
      device_name: deviceName,
    })
    .then((r) => r.data)
}

export function getLoginOptions(email: string) {
  return apiClient.post('/auth/webauthn/login/options', { email }).then((r) => r.data)
}

export function verifyLogin(email: string, credential: unknown) {
  return apiClient
    .post<User>('/auth/webauthn/login/verify', { email, credential })
    .then((r) => r.data)
}

export function listCredentials() {
  return apiClient.get<WebAuthnCredential[]>('/auth/webauthn/credentials').then((r) => r.data)
}

export function deleteCredential(id: number) {
  return apiClient.delete(`/auth/webauthn/credentials/${id}`).then(() => undefined)
}
