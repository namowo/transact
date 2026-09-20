<script setup lang="ts">
import { useThemeStore } from '@/stores/theme'

const theme = useThemeStore()
</script>

<template>
  <UButton
    :icon="theme.isDark ? 'i-lucide-sun' : 'i-lucide-moon'"
    variant="ghost"
    square
    :aria-label="theme.isDark ? 'Switch to light mode' : 'Switch to dark mode'"
    @click="theme.toggle"
  />
</template>
