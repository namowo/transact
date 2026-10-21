<script setup lang="ts">
import { ref } from 'vue'

// A category picker that can also create a new option inline, without
// opening a dialog: type a name that doesn't exist yet, and a "Create ..."
// item appears alongside the filtered matches - picking it creates the
// option immediately and selects it. Uses USelectMenu's built-in
// create-item support rather than faking a fake option in the item list.
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
const open = ref(false)

const creating = ref(false)
const createError = ref('')

async function onCreate(name: string) {
  if (creating.value) return

  creating.value = true
  createError.value = ''
  try {
    const created = await props.create(name)
    modelId.value = created.id
    emit('created', created)
    // The menu doesn't close itself on create (unlike picking an existing
    // option), since nothing here closes it automatically.
    open.value = false
  } catch {
    createError.value = `Could not add "${name}". Please try again.`
  } finally {
    creating.value = false
  }
}
</script>

<template>
  <USelectMenu
    v-model="modelId"
    v-model:open="open"
    :items="options"
    value-key="id"
    label-key="name"
    create-item
    clear
    :placeholder="placeholder ?? 'Select or type to add'"
    :loading="loading || creating"
    :disabled="disabled || creating"
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
  <UAlert v-if="createError" color="error" variant="subtle" :description="createError" />
</template>
