<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { NamedCategory } from '@/api/types'

const props = defineProps<{
  label: string
  api: {
    list: () => Promise<NamedCategory[]>
    create: (payload: { name?: string | null; description?: string | null }) => Promise<NamedCategory>
  }
  placeholder?: string
}>()

const modelValue = defineModel<string[]>({ default: () => [] })

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

async function onCreate(name: string) {
  const created = await props.api.create({ name })
  options.value = [...options.value, created]
  modelValue.value = [...modelValue.value, created.id]
}
</script>

<template>
  <UFormField :ui="{ labelWrapper: 'flex-wrap' }">
    <template #label>
      <span class="whitespace-normal wrap-break-word">{{ label }}</span>
    </template>
    <USelectMenu
      v-model="modelValue"
      :items="options"
      label-key="name"
      value-key="id"
      multiple
      create-item
      :placeholder="placeholder ?? 'Select options'"
      :loading="loading"
      class="w-full"
      :ui="{
        content: 'w-(--reka-combobox-trigger-width)',
        item: 'items-start',
        itemWrapper: 'min-w-0',
        itemLabel: 'whitespace-normal break-words',
      }"
      @create="onCreate"
    >
      <template #create-item-label="{ item }">
        <span class="flex items-center gap-2">
          <UIcon name="i-lucide-plus" class="text-sm" />
          Add "{{ item }}"
        </span>
      </template>
    </USelectMenu>
  </UFormField>
</template>
