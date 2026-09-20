import 'primeicons/primeicons.css'
import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'openvue/config'
import { definePreset } from '@openvue/themes'
import Aura from '@openvue/themes/aura'
import ui from '@nuxt/ui/vue-plugin'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const AppTheme = definePreset(Aura, {
  semantic: {
    primary: {
      50: '{teal.50}',
      100: '{teal.100}',
      200: '{teal.200}',
      300: '{teal.300}',
      400: '{teal.400}',
      500: '{teal.500}',
      600: '{teal.600}',
      700: '{teal.700}',
      800: '{teal.800}',
      900: '{teal.900}',
      950: '{teal.950}',
    },
  },
})

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(PrimeVue, {
  // Each developer/deployer supplies their own free PrimeVue community
  // license via VITE_PRIMEVUE_LICENSE_KEY in a git-ignored .env.local -
  // never commit a license key to the repo. The app works fine without
  // one; PrimeVue just shows a small watermark badge.
  license: import.meta.env.VITE_PRIMEVUE_LICENSE_KEY,
  theme: {
    preset: AppTheme,
    options: {
      darkModeSelector: '.dark',
    },
  },
})
app.use(ui)

// Hydrate the current user from a persisted token, if any, before the
// first render so guarded routes/components don't flash empty state.
const authStore = useAuthStore()
authStore.ensureUserLoaded().finally(() => {
  app.mount('#app')
})
