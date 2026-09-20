<script setup lang="ts" generic="T extends { id: string }">
import { computed } from 'vue'

const props = defineProps<{
  modelValue: string | null
  label: string
  options: T[]
  optionLabel: (option: T) => string
  placeholder?: string
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string | null]
}>()

// USelect's label-key only supports a plain field lookup, not a callback
// like PrimeVue's option-label, so precompute the display label per item.
const items = computed(() => props.options.map((option) => ({ ...option, label: props.optionLabel(option) })))
</script>

<template>
  <div class="flex flex-col gap-2">
    <label class="font-medium text-sm">{{ label }}</label>
    <USelectMenu
      :model-value="modelValue"
      :items="items"
      value-key="id"
      :placeholder="placeholder ?? 'Select an option'"
      :loading="loading"
      clear
      class="w-full"
      @update:model-value="emit('update:modelValue', $event)"
    />
  </div>
</template>
