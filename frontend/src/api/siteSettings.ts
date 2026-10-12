import apiClient from './client'
import type { SiteSettings, SiteSettingsInput } from './types'

export const siteSettingsApi = {
  get: () => apiClient.get<SiteSettings>('/site-settings').then((r) => r.data),
  update: (payload: SiteSettingsInput) =>
    apiClient.patch<SiteSettings>('/site-settings', payload).then((r) => r.data),
}
