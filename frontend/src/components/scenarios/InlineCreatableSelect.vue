<script setup lang="ts">
import { computed, ref } from 'vue'

// A category picker that can also create a new option inline, without
// opening a dialog: type a name that doesn't exist yet, and an "Add ..."
// item appears alongside the filtered matches - picking it creates the
// option immediately and selects it.
type Option = { id: string; name: string; isCreateOption?: boolean }

const props = defineProps<{
  options: { id: string; name?: string | null }[]
  placeholder?: string
  loading?: boolean
  disabled?: boolean
  create: (name: string) => Promise<{ id: string; name?: string | null }>
}>()

const emit = defineEmits<{
  created: [option: { id: string; name?: string | null }]
}>()

const modelId = defineModel<string | null>({ default: null })

const searchTerm = ref('')
const creating = ref(false)
const createError = ref('')

const items = computed<Option[]>(() => {
  const term = searchTerm.value.trim().toLowerCase()
  const matches = props.options
    .filter((option) => (option.name ?? '').trim().toLowerCase().includes(term))
    .map((option) => ({ id: option.id, name: option.name ?? '' }))

  // Never offer to create a name that already exists (case/whitespace
  // insensitively) - the user should just pick the existing option instead
  // of accidentally adding a duplicate.
  const exactMatch = props.options.some(
    (option) => (option.name ?? '').trim().toLowerCase() === term,
  )

  return term && !exactMatch
    ? [...matches, { id: '', name: searchTerm.value.trim(), isCreateOption: true }]
    : matches
})

async function onSelect(option: Option) {
  if (!option.isCreateOption) {
    modelId.value = option.id
    return
  }

  if (creating.value) return

  creating.value = true
  createError.value = ''
  try {
    const created = await props.create(option.name)
    modelId.value = created.id
    emit('created', created)
  } catch {
    createError.value = `Could not add "${option.name}". Please try again.`
  } finally {
    creating.value = false
  }
}

function onUpdateOpen(open: boolean) {
  if (!open) searchTerm.value = ''
}
</script>

<template>
  <USelectMenu
    :model-value="modelId"
    v-model:search-term="searchTerm"
    :items="items"
    value-key="id"
    label-key="name"
    ignore-filter
    clear
    :placeholder="placeholder ?? 'Select or type to add'"
    :loading="loading || creating"
    :disabled="disabled || creating"
    class="w-full"
    @update:open="onUpdateOpen"
    @update:model-value="
      (id: string | null) => {
        const option = items.find((o) => o.id === id)
        if (option) onSelect(option)
      }
    "
    @clear="modelId = null"
  >
    <template #item-label="{ item }">
      <span v-if="item.isCreateOption" class="flex items-center gap-2">
        <UIcon name="i-lucide-plus" class="text-sm" />
        Add "{{ item.name }}"
      </span>
      <span v-else>{{ item.name }}</span>
    </template>
  </USelectMenu>
  <UAlert v-if="createError" color="error" variant="subtle" :description="createError" />
</template>
