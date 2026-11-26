import apiClient from './client'
import type {
  AuthConfig,
  RecoveryCodes,
  RegisterPayload,
  SetupStatus,
  SuperuserSetupPayload,
  TotpSetup,
  TwoFactorChallenge,
  User,
} from './types'

export function fetchAuthConfig() {
  return apiClient.get<AuthConfig>('/auth/config').then((r) => r.data)
}

export function register(payload: RegisterPayload) {
  return apiClient.post<User>('/auth/register', payload).then((r) => r.data)
}

export function fetchSetupStatus() {
  return apiClient.get<SetupStatus>('/auth/setup-status').then((r) => r.data)
}

export function setup(payload: SuperuserSetupPayload) {
  return apiClient.post<User>('/auth/setup', payload).then((r) => r.data)
}

export function login(email: string, password: string) {
  const form = new URLSearchParams()
  form.set('username', email)
  form.set('password', password)
  return apiClient
    .post<User | TwoFactorChallenge>('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    .then((r) => r.data)
}

// Finishes a password login with a code from the authenticator app, or a
// recovery code.
export function loginTwoFactor(loginToken: string, code: string) {
  return apiClient
    .post<User>('/auth/login/two-factor', { login_token: loginToken, code })
    .then((r) => r.data)
}

export function startTotpSetup() {
  return apiClient.post<TotpSetup>('/auth/two-factor/totp/setup').then((r) => r.data)
}

export function enableTotp(code: string) {
  return apiClient.post<RecoveryCodes>('/auth/two-factor/totp/enable', { code }).then((r) => r.data)
}

export function disableTotp(currentPassword: string, code: string) {
  return apiClient
    .post('/auth/two-factor/totp/disable', { current_password: currentPassword, code })
    .then(() => undefined)
}

export function regenerateRecoveryCodes(code: string) {
  return apiClient
    .post<RecoveryCodes>('/auth/two-factor/recovery-codes', { code })
    .then((r) => r.data)
}

export function logout() {
  return apiClient.post('/auth/logout').then(() => undefined)
}

export function verifyEmail(token: string) {
  return apiClient.post<{ message: string }>('/auth/verify-email', { token }).then((r) => r.data)
}

export function resendVerification(email: string) {
  return apiClient
    .post<{ message: string }>('/auth/resend-verification', { email })
    .then((r) => r.data)
}

export function forgotPassword(email: string) {
  return apiClient.post<{ message: string }>('/auth/forgot-password', { email }).then((r) => r.data)
}

export function resetPassword(token: string, newPassword: string) {
  return apiClient
    .post<{ message: string }>('/auth/reset-password', {
      token,
      new_password: newPassword,
    })
    .then((r) => r.data)
}

export function fetchMe() {
  return apiClient.get<User>('/users/me').then((r) => r.data)
}

// Sets the invited user's password and logs them in.
export function acceptInvitation(token: string, password: string) {
  return apiClient.post<User>('/auth/accept-invitation', { token, password }).then((r) => r.data)
}
