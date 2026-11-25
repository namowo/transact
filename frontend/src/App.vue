<script setup lang="ts">
import { computed } from 'vue'
import { RouterView } from 'vue-router'
import { en } from '@nuxt/ui/locale'
import { useAuthStore } from '@/stores/auth'

// Keeps the interface texts in English but follows the user's locale for
// number input (decimal separator) and date formats.
const auth = useAuthStore()
const appLocale = computed(() => ({ ...en, code: auth.locale }))
</script>

<template>
  <UApp :locale="appLocale">
    <RouterView />
  </UApp>
</template>
