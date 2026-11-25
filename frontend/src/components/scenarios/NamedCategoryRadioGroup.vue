<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { NamedCategory } from '@/api/types'

// A radio-group alternative to CategorySelect for small, fixed-ish category
// sets (sex, DNA shedding propensity, ...): shows every option as a card
// with an icon so the common case needs one click instead of opening a
// dropdown. Clicking the already-selected option clears it again.
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
  // When set, an extra option with this label is shown that stands for
  // "no value" (null), so users can explicitly pick e.g. "Not determined"
  // or undo an accidental selection.
  noneLabel?: string
  noneIcon?: string
}>()

// Radio items need a non-null value, so null is mapped to a sentinel.
const NONE_VALUE = '__none__'

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

const radioItems = computed(() => {
  const items = options.value.map((option) => ({
    value: option.id,
    label: option.name ?? `#${option.id}`,
    icon: (option.name && props.icons?.[option.name.toLowerCase()]) || props.defaultIcon,
  }))
  if (props.noneLabel) {
    items.push({
      value: NONE_VALUE,
      label: props.noneLabel,
      icon: props.noneIcon ?? 'i-lucide-circle-help',
    })
  }
  return items
})

const radioValue = computed<string | undefined>({
  get: () => modelValue.value ?? (props.noneLabel ? NONE_VALUE : undefined),
  set: (value) => {
    modelValue.value = !value || value === NONE_VALUE ? null : value
  },
})

// Clicking the already-selected card clears it. Native radios can't be
// unselected by clicking them again, so intercept the click in the capture
// phase before it reaches the radio and reset the value ourselves.
function onClickCapture(event: MouseEvent) {
  if (loading.value || modelValue.value == null) return
  const item = (event.target as HTMLElement | null)?.closest('[data-slot="item"]')
  const radio = item?.querySelector('[role="radio"]')
  if (radio?.getAttribute('aria-checked') !== 'true') return
  event.preventDefault()
  event.stopPropagation()
  modelValue.value = null
}
</script>

<template>
  <UFormField :label="label" :hint="hint">
    <!-- Wrapper element so the capture listener sees clicks before the radios do. -->
    <div @click.capture="onClickCapture">
    <URadioGroup
      v-model="radioValue"
      :items="radioItems"
      :disabled="loading"
      :variant="variant ?? 'table'"
      :indicator="(variant ?? 'table') === 'list' ? undefined : 'hidden'"
      :orientation="orientation ?? ((variant ?? 'table') === 'list' ? 'vertical' : 'horizontal')"
      :class="(orientation ?? 'horizontal') === 'horizontal' ? 'flex-wrap' : undefined"
      :ui="(variant ?? 'table') === 'list' ? undefined : { fieldset: 'flex-wrap', item: 'items-center text-center' }"
    />
    </div>
  </UFormField>
</template>
