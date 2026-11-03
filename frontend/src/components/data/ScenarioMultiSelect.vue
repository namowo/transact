<script setup lang="ts">
import type { Scenario } from '@/api/types'

// Which of the study's scenarios a piece of data (individual, item) is used
// in. Individuals and items can be shared across several scenarios.
defineProps<{ scenarios: Scenario[]; label?: string }>()

const modelValue = defineModel<string[]>({ default: () => [] })
</script>

<template>
  <UFormField :label="label ?? 'Scenarios'" hint="Leave empty to use in all scenarios">
    <USelectMenu
      v-model="modelValue"
      :items="scenarios"
      value-key="id"
      label-key="name"
      multiple
      placeholder="Select scenarios"
      class="w-full"
    />
  </UFormField>
</template>
