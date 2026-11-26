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
import type {
  AuthConfig,
  Permission,
  RegisterPayload,
  SuperuserSetupPayload,
  TwoFactorChallenge,
  User,
} from '@/api/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const needsSetup = ref(false)
  // Sign-up and sign-in policy. Until it's loaded, assume the defaults.
  const config = ref<AuthConfig>({
    registration_enabled: true,
    invitations_enabled: true,
    two_factor_required: false,
  })

  const isAuthenticated = computed(() => !!user.value)

  // Whether the user's groups grant `permission`. Laboratory permissions
  // (lab.*, data.enter) only apply to the user's own laboratory.
  function can(permission: Permission) {
    return !!user.value?.permissions?.includes(permission)
  }
  function canAny(...permissions: Permission[]) {
    return permissions.some(can)
  }

  const canQualityCheck = computed(() => can('studies.quality_check'))
  // Manages the members of their own laboratory.
  const isLabAdmin = computed(() => can('lab.manage_members'))
  // Sees the admin area: anything platform-wide to manage.
  const isAdmin = computed(() =>
    canAny(
      'users.manage',
      'groups.manage',
      'laboratories.manage',
      'site_settings.manage',
      'catalog.delete',
    ),
  )

  // How numbers are typed and shown (BCP 47 tag from the user's profile).
  const locale = computed(() => user.value?.locale || 'en-US')
  const decimalSeparator = computed<'.' | ','>(() => {
    const part = new Intl.NumberFormat(locale.value)
      .formatToParts(1.1)
      .find((p) => p.type === 'decimal')
    return part?.value === ',' ? ',' : '.'
  })

  // Formats a number for display in the user's locale (e.g. 0,1 in de-DE).
  function formatNumber(
    value: number,
    options: Intl.NumberFormatOptions = { maximumFractionDigits: 6 },
  ) {
    return new Intl.NumberFormat(locale.value, options).format(value)
  }

  let userLoadedPromise: Promise<void> | null = null
  let setupStatusPromise: Promise<void> | null = null

  // Returns the challenge when a second factor is needed to finish signing
  // in (see `loginTwoFactor`), else signs in.
  async function login(email: string, password: string): Promise<TwoFactorChallenge | null> {
    const result = await authApi.login(email, password)
    if ('two_factor_required' in result) return result
    user.value = result
    userLoadedPromise = Promise.resolve()
    return null
  }

  async function loginTwoFactor(loginToken: string, code: string) {
    user.value = await authApi.loginTwoFactor(loginToken, code)
    userLoadedPromise = Promise.resolve()
  }

  async function acceptInvitation(token: string, password: string) {
    user.value = await authApi.acceptInvitation(token, password)
    userLoadedPromise = Promise.resolve()
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
    const [status, authConfig] = await Promise.allSettled([
      authApi.fetchSetupStatus(),
      authApi.fetchAuthConfig(),
    ])
    needsSetup.value = status.status === 'fulfilled' ? status.value.needs_setup : false
    if (authConfig.status === 'fulfilled') config.value = authConfig.value
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
    config,
    isAuthenticated,
    can,
    canAny,
    isAdmin,
    canQualityCheck,
    isLabAdmin,
    locale,
    decimalSeparator,
    formatNumber,
    login,
    loginTwoFactor,
    acceptInvitation,
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
