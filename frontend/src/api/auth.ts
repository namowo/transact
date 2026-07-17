import apiClient from './client'
import type { RegisterPayload, Token, User } from './types'

export function register(payload: RegisterPayload) {
  return apiClient.post<User>('/auth/register', payload).then((r) => r.data)
}

export function login(email: string, password: string) {
  const form = new URLSearchParams()
  form.set('username', email)
  form.set('password', password)
  return apiClient
    .post<Token>('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    .then((r) => r.data)
}

export function verifyEmail(token: string) {
  return apiClient
    .post<{ message: string }>('/auth/verify-email', { token })
    .then((r) => r.data)
}

export function resendVerification(email: string) {
  return apiClient
    .post<{ message: string }>('/auth/resend-verification', { email })
    .then((r) => r.data)
}

export function forgotPassword(email: string) {
  return apiClient
    .post<{ message: string }>('/auth/forgot-password', { email })
    .then((r) => r.data)
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
