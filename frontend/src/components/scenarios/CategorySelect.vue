<script setup lang="ts">
import { onMounted, ref } from 'vue'
import InlineCreatableSelect from './InlineCreatableSelect.vue'
import type { NamedCategory } from '@/api/types'

const props = defineProps<{
  label: string
  hint?: string
  description?: string
  api: {
    list: () => Promise<NamedCategory[]>
    create: (payload: {
      name?: string | null
      description?: string | null
    }) => Promise<NamedCategory>
  }
  placeholder?: string
  allowAdd?: boolean
  disabled?: boolean
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

async function createOption(name: string) {
  const created = await props.api.create({ name })
  options.value = [...options.value, created]
  return created
}
</script>

<template>
  <UFormField :hint="hint">
    <template #label>
      <div class="flex items-center gap-1.5">
        <span>{{ label }}</span>
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
    <InlineCreatableSelect
      v-if="allowAdd ?? true"
      v-model="modelValue"
      :options="options"
      :loading="loading"
      :disabled="disabled"
      :placeholder="placeholder ?? 'Select or type to add'"
      :create="createOption"
    />
    <USelectMenu
      v-else
      v-model="modelValue"
      :items="options"
      label-key="name"
      value-key="id"
      :placeholder="placeholder ?? 'Select an option'"
      :loading="loading"
      :disabled="disabled"
      clear
      class="w-full"
    />
  </UFormField>
</template>
