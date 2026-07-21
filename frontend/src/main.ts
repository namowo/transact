import 'primeicons/primeicons.css'
import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import ToastService from 'primevue/toastservice'
import ConfirmationService from 'primevue/confirmationservice'
import { definePreset } from '@primeuix/themes'
import Aura from '@primeuix/themes/aura'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const AppTheme = definePreset(Aura, {
  semantic: {
    primary: {
      50: '{blue.50}',
      100: '{blue.100}',
      200: '{blue.200}',
      300: '{blue.300}',
      400: '{blue.400}',
      500: '{blue.500}',
      600: '{blue.600}',
      700: '{blue.700}',
      800: '{blue.800}',
      900: '{blue.900}',
      950: '{blue.950}',
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
      darkModeSelector: '.app-dark',
    },
  },
})
app.use(ToastService)
app.use(ConfirmationService)

// Hydrate the current user from a persisted token, if any, before the
// first render so guarded routes/components don't flash empty state.
const authStore = useAuthStore()
authStore.ensureUserLoaded().finally(() => {
  app.mount('#app')
})
