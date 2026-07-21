<script setup lang="ts" generic="T extends { id: number }">
import Select from 'primevue/select'

defineProps<{
  modelValue: number | null
  label: string
  options: T[]
  optionLabel: (option: T) => string
  placeholder?: string
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number | null]
}>()
</script>

<template>
  <div class="flex flex-col gap-2">
    <label class="font-medium text-sm">{{ label }}</label>
    <Select
      :model-value="modelValue"
      :options="options"
      :option-label="optionLabel"
      option-value="id"
      :placeholder="placeholder ?? 'Select an option'"
      :loading="loading"
      show-clear
      filter
      fluid
      @update:model-value="emit('update:modelValue', $event)"
    />
  </div>
</template>
