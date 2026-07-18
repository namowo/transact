<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import ThemeToggle from '@/components/ThemeToggle.vue'
import { useThemeStore } from '@/stores/theme'

const theme = useThemeStore()
</script>

<template>
  <div class="relative grid min-h-full lg:grid-cols-2 bg-surface-0 dark:bg-surface-950">
    <div class="absolute top-4 right-4 z-10">
      <ThemeToggle />
    </div>

    <div class="flex flex-col gap-4 p-6 md:p-10">
      <RouterLink
        to="/"
        class="flex items-center gap-2 justify-center md:justify-start no-underline"
      >
        <img
          :src="theme.isDark ? '/transact_logo_light.png' : '/transact_logo_dark.png'"
          alt="TransAct"
          class="size-7"
        />
        <span class="font-semibold text-surface-900 dark:text-surface-0">TransAct</span>
      </RouterLink>

      <div class="flex flex-1 items-center justify-center">
        <div class="w-full max-w-sm">
          <RouterView />
        </div>
      </div>
    </div>

    <div class="relative hidden overflow-hidden bg-surface-100 dark:bg-surface-900 lg:block">
      <div
        class="absolute inset-0 opacity-60 bg-[radial-gradient(var(--p-surface-300)_1px,transparent_1px)] bg-size-[24px_24px] dark:bg-[radial-gradient(var(--p-surface-700)_1px,transparent_1px)]"
      />
      <div class="absolute -top-32 -right-24 size-96 rounded-full bg-primary/20 blur-3xl" />
      <div class="absolute -bottom-32 -left-24 size-96 rounded-full bg-primary/10 blur-3xl" />

      <div class="relative flex h-full flex-col items-center justify-center gap-4 p-10 text-center">
        <img
          :src="theme.isDark ? '/transact_logo_light.png' : '/transact_logo_dark.png'"
          alt="TransAct"
          class="size-16"
        />
        <h2 class="text-2xl font-semibold text-surface-900 dark:text-surface-0">TransAct</h2>
        <p class="max-w-xs text-sm text-surface-600 dark:text-surface-300">
          Manage your laboratory's samples, methods, and recovery workflows in one place.
        </p>
      </div>
    </div>
  </div>
</template>
