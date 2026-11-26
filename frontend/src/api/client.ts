import axios from 'axios'
import { startGlobalLoading } from '@/composables/useGlobalLoading'

declare module 'axios' {
  interface AxiosRequestConfig {
    /** Don't show the global progress bar for this request (background polling). */
    silent?: boolean
  }
  interface InternalAxiosRequestConfig {
    _stopLoading?: () => void
  }
}

// Must match TWO_FACTOR_SETUP_REQUIRED in backend/app/core/deps.py.
export const TWO_FACTOR_SETUP_REQUIRED = 'Set up two-factor authentication to continue.'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  withCredentials: true,
})

apiClient.interceptors.request.use((config) => {
  if (!config.silent) config._stopLoading = startGlobalLoading()
  return config
})

apiClient.interceptors.response.use(
  (response) => {
    response.config._stopLoading?.()
    return response
  },
  async (error) => {
    error.config?._stopLoading?.()
    if (error.response?.status === 401) {
      const { useAuthStore } = await import('@/stores/auth')
      useAuthStore().handleUnauthorized()
      const { default: router } = await import('@/router')
      if (router.currentRoute.value.meta.requiresAuth) {
        router.push({
          name: 'login',
          query: { redirect: router.currentRoute.value.fullPath },
        })
      }
    }
    if (
      error.response?.status === 403 &&
      error.response.data?.detail === TWO_FACTOR_SETUP_REQUIRED
    ) {
      // The session may only set up a second factor (e.g. two-factor
      // authentication became required while signed in).
      const { useAuthStore } = await import('@/stores/auth')
      await useAuthStore().fetchCurrentUser()
      const { default: router } = await import('@/router')
      if (router.currentRoute.value.name !== 'two-factor-setup') {
        router.push({
          name: 'two-factor-setup',
          query: { redirect: router.currentRoute.value.fullPath },
        })
      }
    }
    return Promise.reject(error)
  },
)

export default apiClient
