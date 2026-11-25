import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ui from '@nuxt/ui/vue-plugin'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ui)

// Hydrate the current user from a persisted token, if any, before the
// first render so guarded routes/components don't flash empty state.
const authStore = useAuthStore()
authStore.ensureUserLoaded().finally(() => {
  app.mount('#app')
})
