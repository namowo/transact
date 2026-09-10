<script setup lang="ts">
import { ref, watch } from 'vue'
import AutoComplete from 'primevue/autocomplete'
import Message from 'primevue/message'

// A category picker that can also create a new option inline, without
// opening a dialog: type a name that doesn't exist yet, and an "Add ..."
// suggestion appears alongside the filtered matches - picking it creates the
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

// Bound to the actual selected option object (not just its id/name) since
// AutoComplete's own duplicate-selection guard (relevant for forceSelection)
// compares this against the option - a plain string here would always
// mismatch and the guard would never kick in, causing double submits.
const selected = ref<Option | null>(null)
const suggestions = ref<Option[]>([])
const creating = ref(false)
const createError = ref('')

watch(
  () => modelId.value,
  (id) => {
    const option = props.options.find((o) => o.id === id)
    selected.value = option ? { id: option.id, name: option.name ?? '' } : null
  },
  { immediate: true },
)

function search(event: { query: string }) {
  const term = event.query.trim().toLowerCase()
  const matches = props.options
    .filter((option) => (option.name ?? '').trim().toLowerCase().includes(term))
    .map((option) => ({ id: option.id, name: option.name ?? '' }))

  // Never offer to create a name that already exists (case/whitespace
  // insensitively) - the user should just pick the existing option instead
  // of accidentally adding a duplicate.
  const exactMatch = props.options.some(
    (option) => (option.name ?? '').trim().toLowerCase() === term,
  )

  suggestions.value =
    term && !exactMatch
      ? [...matches, { id: '', name: event.query.trim(), isCreateOption: true }]
      : matches
}

async function onSelect(event: { value: Option }) {
  const selection = event.value
  if (!selection.isCreateOption) {
    modelId.value = selection.id
    return
  }

  // AutoComplete's forceSelection mode can call this handler a second time
  // for the same click (e.g. once on click, once again when the input
  // blurs) - ignore any re-entrant call while a create is already in
  // flight, so one click can't submit two identical creates.
  if (creating.value) return

  creating.value = true
  createError.value = ''
  try {
    const created = await props.create(selection.name)
    modelId.value = created.id
    emit('created', created)
  } catch {
    createError.value = `Could not add "${selection.name}". Please try again.`
    // Revert the input back to whatever was actually selected before this
    // failed attempt, since the create-option is no longer valid.
    const option = props.options.find((o) => o.id === modelId.value)
    selected.value = option ? { id: option.id, name: option.name ?? '' } : null
  } finally {
    creating.value = false
  }
}

function onClear() {
  modelId.value = null
}
</script>

<template>
  <AutoComplete
    v-model="selected"
    :suggestions="suggestions"
    option-label="name"
    :placeholder="placeholder ?? 'Select or type to add'"
    :loading="loading || creating"
    :disabled="disabled || creating"
    dropdown
    force-selection
    fluid
    @complete="search"
    @option-select="onSelect"
    @clear="onClear"
  >
    <template #option="{ option }">
      <span v-if="option.isCreateOption" class="flex items-center gap-2">
        <i class="pi pi-plus text-sm" />
        Add "{{ option.name }}"
      </span>
      <span v-else>{{ option.name }}</span>
    </template>
  </AutoComplete>
  <Message v-if="createError" severity="error" size="small" variant="simple">{{ createError }}</Message>
</template>
