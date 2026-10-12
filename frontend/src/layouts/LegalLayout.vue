<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import ThemeToggle from '@/components/ThemeToggle.vue'
import { useThemeStore } from '@/stores/theme'

const theme = useThemeStore()
</script>

<template>
  <div class="min-h-full bg-surface-0 dark:bg-surface-950">
    <div class="flex items-center justify-between p-6 max-w-3xl mx-auto">
      <RouterLink to="/" class="flex items-center gap-2 no-underline">
        <img
          :src="theme.isDark ? '/transact_logo_light.png' : '/transact_logo_dark.png'"
          alt="TransAct"
          class="size-7"
        />
        <span class="font-semibold text-surface-900 dark:text-surface-0">TransAct</span>
      </RouterLink>
      <ThemeToggle />
    </div>

    <div class="max-w-3xl mx-auto p-6 pt-0">
      <RouterView />
    </div>
  </div>
</template>
