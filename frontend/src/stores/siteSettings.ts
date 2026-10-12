import { ref } from 'vue'
import { defineStore } from 'pinia'
import { siteSettingsApi } from '@/api/siteSettings'
import type { SiteSettings } from '@/api/types'

export const useSiteSettingsStore = defineStore('siteSettings', () => {
  const settings = ref<SiteSettings | null>(null)
  const loading = ref(false)
  let loaded = false

  async function load(force = false) {
    if (loaded && !force) return
    loading.value = true
    try {
      settings.value = await siteSettingsApi.get()
      loaded = true
    } finally {
      loading.value = false
    }
  }

  return { settings, loading, load }
})
