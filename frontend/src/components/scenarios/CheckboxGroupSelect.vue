<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { NamedCategory } from '@/api/types'

// For a small, fixed set of options where a dropdown just adds an extra
// click - every option is shown directly as a row with a toggle switch.
const props = defineProps<{
  label: string
  api: { list: () => Promise<NamedCategory[]> }
}>()

const modelValue = defineModel<string[]>({ default: () => [] })

const options = ref<NamedCategory[]>([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    options.value = await props.api.list()
  } finally {
    loading.value = false
  }
})

function toggle(id: string, checked: boolean) {
  modelValue.value = checked
    ? [...modelValue.value, id]
    : modelValue.value.filter((v) => v !== id)
}
</script>

<template>
  <div class="flex flex-col gap-2">
    <label class="font-medium text-sm">{{ label }}</label>
    <UCard :ui="{ body: 'p-0 sm:p-0' }">
      <label
        v-for="(option, index) in options"
        :key="option.id"
        class="flex items-center justify-between gap-2 px-4 py-2.5 cursor-pointer"
        :class="index !== options.length - 1 && 'border-b border-default'"
      >
        <span class="text-sm">{{ option.name }}</span>
        <USwitch
          :model-value="modelValue.includes(option.id)"
          @update:model-value="toggle(option.id, $event)"
        />
      </label>
    </UCard>
  </div>
</template>
