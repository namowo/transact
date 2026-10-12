<script setup lang="ts">
import { computed } from 'vue'
import type { DropdownMenuItem } from '@nuxt/ui'
import { useThemeStore } from '@/stores/theme'

const theme = useThemeStore()

type ThemeMode = 'system' | 'light' | 'dark'

const icons: Record<ThemeMode, string> = {
  system: 'i-lucide-monitor',
  light: 'i-lucide-sun',
  dark: 'i-lucide-moon',
}

const labels: Record<ThemeMode, string> = {
  system: 'System',
  light: 'Light',
  dark: 'Dark',
}

const items = computed<DropdownMenuItem[]>(() =>
  (['system', 'light', 'dark'] as const).map((value) => ({
    label: labels[value],
    icon: icons[value],
    type: 'checkbox',
    checked: theme.mode === value,
    onSelect: () => theme.setMode(value),
  })),
)

const currentIcon = computed(() => icons[theme.mode])
</script>

<template>
  <UDropdownMenu :items="items" :content="{ align: 'end' }">
    <UTooltip text="Theme">
      <UButton
        :icon="currentIcon"
        trailing-icon="i-lucide-chevron-down"
        color="neutral"
        variant="ghost"
        size="sm"
        aria-label="Theme"
      />
    </UTooltip>
  </UDropdownMenu>
</template>
