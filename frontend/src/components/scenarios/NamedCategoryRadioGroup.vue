<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { NamedCategory } from '@/api/types'

// A radio-group alternative to CategorySelect for small, fixed-ish category
// sets (sex, DNA shedding propensity, ...): shows every option as a card
// with an icon so the common case needs one click instead of opening a
// dropdown. Clicking the already-selected option clears it, since native
// radios can't be unselected by clicking them again.
const props = defineProps<{
  label: string
  hint?: string
  api: {
    list: () => Promise<NamedCategory[]>
  }
  icons?: Record<string, string>
  defaultIcon?: string
  variant?: 'table' | 'list'
  orientation?: 'horizontal' | 'vertical'
}>()

const modelValue = defineModel<string | null>({ default: null })

const options = ref<NamedCategory[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    options.value = await props.api.list()
  } finally {
    loading.value = false
  }
}

onMounted(load)

const radioItems = computed(() =>
  options.value.map((option) => ({
    value: option.id,
    label: option.name ?? `#${option.id}`,
    icon: (option.name && props.icons?.[option.name.toLowerCase()]) || props.defaultIcon,
  })),
)

function onItemMousedown(value: string) {
  if (modelValue.value === value) {
    // Let the click still happen, then clear right after so the radio
    // doesn't re-select itself.
    requestAnimationFrame(() => {
      modelValue.value = null
    })
  }
}
</script>

<template>
  <UFormField :label="label" :hint="hint">
    <URadioGroup
      v-model="modelValue"
      :items="radioItems"
      :disabled="loading"
      :variant="variant ?? 'table'"
      :indicator="(variant ?? 'table') === 'list' ? undefined : 'hidden'"
      :orientation="orientation ?? ((variant ?? 'table') === 'list' ? 'vertical' : 'horizontal')"
      :class="(orientation ?? 'horizontal') === 'horizontal' ? 'flex-wrap' : undefined"
      :ui="(variant ?? 'table') === 'list' ? undefined : { fieldset: 'flex-wrap', item: 'items-center text-center' }"
    >
      <template #label="{ item }">
        <span @mousedown="onItemMousedown(item.value as string)">{{ item.label }}</span>
      </template>
    </URadioGroup>
  </UFormField>
</template>
