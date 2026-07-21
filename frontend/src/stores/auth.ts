import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import * as authApi from '@/api/auth'
import {
  changeEmail,
  changePassword,
  dismissPasskeyPrompt,
  updateMe,
  type ChangeEmailPayload,
  type ChangePasswordPayload,
  type UpdateProfilePayload,
} from '@/api/users'
import type { RegisterPayload, SuperuserSetupPayload, User } from '@/api/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const needsSetup = ref(false)

  const isAuthenticated = computed(() => !!user.value)
  const isSuperuser = computed(() => !!user.value?.is_superuser)
  const canQualityCheck = computed(
    () => !!user.value?.is_superuser || !!user.value?.can_quality_check,
  )
  const isLabAdmin = computed(
    () => !!user.value?.is_superuser || !!user.value?.can_manage_lab_users,
  )

  let userLoadedPromise: Promise<void> | null = null
  let setupStatusPromise: Promise<void> | null = null

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

  async function fetchSetupStatus() {
    try {
      needsSetup.value = (await authApi.fetchSetupStatus()).needs_setup
    } catch {
      needsSetup.value = false
    }
  }

  // Memoized like ensureUserLoaded - the setup gate only needs to be
  // resolved once per page load, and stops mattering entirely once setup
  // has been completed for the lifetime of the app.
  function ensureSetupStatusLoaded() {
    if (!setupStatusPromise) {
      setupStatusPromise = fetchSetupStatus()
    }
    return setupStatusPromise
  }

  async function completeSetup(payload: SuperuserSetupPayload) {
    user.value = await authApi.setup(payload)
    needsSetup.value = false
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

  async function dismissPasskeyPromptBanner() {
    user.value = await dismissPasskeyPrompt()
    return user.value
  }

  async function changeMyPassword(payload: ChangePasswordPayload) {
    user.value = await changePassword(payload)
    return user.value
  }

  async function changeMyEmail(payload: ChangeEmailPayload) {
    user.value = await changeEmail(payload)
    return user.value
  }

  return {
    user,
    needsSetup,
    isAuthenticated,
    isSuperuser,
    canQualityCheck,
    isLabAdmin,
    login,
    register,
    fetchCurrentUser,
    ensureUserLoaded,
    ensureSetupStatusLoaded,
    completeSetup,
    handleUnauthorized,
    logout,
    updateProfile,
    dismissPasskeyPromptBanner,
    changeMyPassword,
    changeMyEmail,
  }
})
