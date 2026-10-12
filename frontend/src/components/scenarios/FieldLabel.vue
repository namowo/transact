<script setup lang="ts">
defineProps<{
  label: string
  hint?: string
  description?: string
  for?: string
}>()
</script>

<template>
  <UTooltip
    v-if="description"
    :text="description"
    :content="{ side: 'top' }"
    :ui="{
      content: 'max-w-sm h-auto py-2',
      text: 'whitespace-normal text-wrap',
    }"
  >
    <div class="flex items-center gap-1.5 cursor-help">
      <label :for="$props.for" class="font-medium text-sm">{{ label }}</label>
      <span v-if="hint" class="text-xs text-surface-500 dark:text-surface-400">{{ hint }}</span>
      <UIcon name="i-lucide-info" class="text-surface-500 dark:text-surface-400 text-sm" />
    </div>
  </UTooltip>
  <div v-else class="flex items-center gap-1.5">
    <label :for="$props.for" class="font-medium text-sm">{{ label }}</label>
    <span v-if="hint" class="text-xs text-surface-500 dark:text-surface-400">{{ hint }}</span>
  </div>
</template>
