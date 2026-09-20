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
    <UTooltip
      v-if="description"
      :text="description"
      :content="{ side: 'top' }"
      :ui="{ content: 'max-w-xs' }"
    >
      <UIcon
        name="i-lucide-info"
        class="text-surface-500 dark:text-surface-400 text-sm cursor-help"
      />
    </UTooltip>
  </div>
</template>
