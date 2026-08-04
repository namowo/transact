<script setup lang="ts">
defineProps<{
  label: string
  description?: string
  for?: string
}>()
</script>

<template>
  <div class="flex items-center gap-1.5">
    <label :for="$props.for" class="font-medium text-sm">{{ label }}</label>
    <i
      v-if="description"
      v-tooltip.top="{ value: description, pt: { text: { class: 'max-w-xs' } } }"
      class="pi pi-info-circle text-surface-500 dark:text-surface-400 text-sm cursor-help"
    />
  </div>
</template>
