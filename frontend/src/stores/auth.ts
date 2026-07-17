import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import * as authApi from '@/api/auth'
import { updateMe, type UpdateProfilePayload } from '@/api/users'
import { clearToken, getToken, setToken } from '@/api/token'
import type { RegisterPayload, User } from '@/api/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(getToken())
  const user = ref<User | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(email: string, password: string) {
    const result = await authApi.login(email, password)
    token.value = result.access_token
    setToken(result.access_token)
    await fetchCurrentUser()
  }

  function register(payload: RegisterPayload) {
    return authApi.register(payload)
  }

  async function fetchCurrentUser() {
    if (!token.value) return
    user.value = await authApi.fetchMe()
  }

  function logout() {
    token.value = null
    user.value = null
    clearToken()
  }

  async function updateProfile(payload: UpdateProfilePayload) {
    user.value = await updateMe(payload)
    return user.value
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    register,
    fetchCurrentUser,
    logout,
    updateProfile,
  }
})
