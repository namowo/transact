<script setup lang="ts">
import type { Scenario } from '@/api/types'

// Which of the study's scenarios a piece of data (individual, item) is used
// in. Individuals and items can be shared across several scenarios and must
// be in at least one (`required`).
defineProps<{ scenarios: Scenario[]; label?: string; required?: boolean; error?: string | boolean }>()

const modelValue = defineModel<string[]>({ default: () => [] })
</script>

<template>
  <UFormField
    :label="label ?? 'Scenarios'"
    :hint="required ? undefined : 'Leave empty to use in all scenarios'"
    :required="required"
    :error="error"
  >
    <USelectMenu
      v-model="modelValue"
      :items="scenarios"
      value-key="id"
      label-key="name"
      multiple
      placeholder="Select scenarios"
      clear
      class="w-full"
    />
  </UFormField>
</template>
