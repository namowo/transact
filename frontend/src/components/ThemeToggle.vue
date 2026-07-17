<script setup lang="ts">
import Button from 'primevue/button'
import { useThemeStore } from '@/stores/theme'

const theme = useThemeStore()
</script>

<template>
  <Button
    :icon="theme.isDark ? 'pi pi-sun' : 'pi pi-moon'"
    text
    rounded
    :aria-label="theme.isDark ? 'Switch to light mode' : 'Switch to dark mode'"
    @click="theme.toggle"
  />
</template>
