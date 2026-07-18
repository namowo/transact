import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import * as authApi from '@/api/auth'
import { updateMe, type UpdateProfilePayload } from '@/api/users'
import type { RegisterPayload, User } from '@/api/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)

  const isAuthenticated = computed(() => !!user.value)

  let userLoadedPromise: Promise<void> | null = null

  async function login(email: string, password: string) {
    user.value = await authApi.login(email, password)
  }

  function register(payload: RegisterPayload) {
    return authApi.register(payload)
  }

  async function fetchCurrentUser() {
    try {
      user.value = await authApi.fetchMe()
    } catch {
      user.value = null
    }
  }

  // The session lives in an httpOnly cookie the frontend can't read, so the
  // only way to know whether it's still valid is to ask the backend. This is
  // memoized so route guards can await it on every navigation without
  // refetching once it has resolved.
  function ensureUserLoaded() {
    if (!userLoadedPromise) {
      userLoadedPromise = fetchCurrentUser()
    }
    return userLoadedPromise
  }

  // Called by the API client's 401 response interceptor - clears local
  // state without hitting the network again, since the cookie is already
  // gone/expired at that point.
  function handleUnauthorized() {
    user.value = null
    userLoadedPromise = Promise.resolve()
  }

  async function logout() {
    try {
      await authApi.logout()
    } finally {
      user.value = null
      userLoadedPromise = null
    }
  }

  async function updateProfile(payload: UpdateProfilePayload) {
    user.value = await updateMe(payload)
    return user.value
  }

  return {
    user,
    isAuthenticated,
    login,
    register,
    fetchCurrentUser,
    ensureUserLoaded,
    handleUnauthorized,
    logout,
    updateProfile,
  }
})
