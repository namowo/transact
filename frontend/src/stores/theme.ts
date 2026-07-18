import { ref, watchEffect } from 'vue'
import { defineStore } from 'pinia'

const STORAGE_KEY = 'transact-theme'

function getInitialIsDark() {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored) return stored === 'dark'
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

export const useThemeStore = defineStore('theme', () => {
  const isDark = ref(getInitialIsDark())

  watchEffect(() => {
    document.documentElement.classList.toggle('app-dark', isDark.value)
    localStorage.setItem(STORAGE_KEY, isDark.value ? 'dark' : 'light')

    const favicon = document.getElementById('favicon') as HTMLLinkElement | null
    if (favicon) {
      favicon.href = isDark.value ? '/transact_logo_light.png' : '/transact_logo_dark.png'
    }
  })

  function toggle() {
    isDark.value = !isDark.value
  }

  return { isDark, toggle }
})
