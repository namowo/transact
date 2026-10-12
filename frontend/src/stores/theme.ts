import { computed, ref, watchEffect } from 'vue'
import { defineStore } from 'pinia'

const STORAGE_KEY = 'transact-theme'

type ThemeMode = 'system' | 'light' | 'dark'

function getInitialMode(): ThemeMode {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored === 'light' || stored === 'dark' || stored === 'system') return stored
  return 'system'
}

const media = window.matchMedia('(prefers-color-scheme: dark)')

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<ThemeMode>(getInitialMode())
  const systemPrefersDark = ref(media.matches)

  media.addEventListener('change', (e) => {
    systemPrefersDark.value = e.matches
  })

  const isDark = computed(() =>
    mode.value === 'system' ? systemPrefersDark.value : mode.value === 'dark',
  )

  watchEffect(() => {
    document.documentElement.classList.toggle('dark', isDark.value)
    localStorage.setItem(STORAGE_KEY, mode.value)

    const favicon = document.getElementById('favicon') as HTMLLinkElement | null
    if (favicon) {
      favicon.href = isDark.value ? '/transact_logo_light.png' : '/transact_logo_dark.png'
    }
  })

  function setMode(next: ThemeMode) {
    mode.value = next
  }

  return { mode, isDark, setMode }
})
