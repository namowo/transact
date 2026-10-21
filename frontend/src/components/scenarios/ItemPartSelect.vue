<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import InlineCreatableSelect from './InlineCreatableSelect.vue'
import { itemPartsCategoryApi } from '@/api/categories'
import type { ItemPartsCategory } from '@/api/types'

// An item part belongs to exactly one item category - this picker only
// offers parts scoped to whichever category the parent form passes in
// (derived from the selected item), mirroring how ItemCategoryFields scopes
// subcategories to a category.
const props = defineProps<{
  itemCategoryId: string | null
  disabled?: boolean
}>()

const partId = defineModel<string | null>({ default: null })

const allParts = ref<ItemPartsCategory[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    allParts.value = await itemPartsCategoryApi.list()
  } finally {
    loading.value = false
  }
}

onMounted(load)

const availableParts = computed(() =>
  allParts.value.filter((part) => part.item_category_id === props.itemCategoryId),
)

const selectedPart = computed(
  () => allParts.value.find((part) => part.id === partId.value) ?? null,
)

// If the item category changes out from under the current selection (e.g.
// the user picks a different item in a different category), the old part
// no longer applies - clear it rather than silently keeping a cross-category
// reference.
const itemCategoryIdAtStart = ref(props.itemCategoryId)
watch(
  () => props.itemCategoryId,
  (current) => {
    if (current !== itemCategoryIdAtStart.value) {
      partId.value = null
      itemCategoryIdAtStart.value = current
    }
  },
)

async function createPart(name: string) {
  if (props.itemCategoryId === null) throw new Error('No item category available')
  const created = await itemPartsCategoryApi.create({ name, item_category_id: props.itemCategoryId })
  allParts.value = [...allParts.value, created]
  return created
}

const showEditDialog = ref(false)
const editName = ref('')
const editDescription = ref('')
const editError = ref('')
const saving = ref(false)

function openEditDialog() {
  if (!selectedPart.value) return
  editName.value = selectedPart.value.name ?? ''
  editDescription.value = selectedPart.value.description ?? ''
  editError.value = ''
  showEditDialog.value = true
}

async function saveEdit() {
  if (!selectedPart.value) return
  if (!editName.value.trim()) {
    editError.value = 'Name is required.'
    return
  }

  saving.value = true
  editError.value = ''
  try {
    const updated = await itemPartsCategoryApi.update(selectedPart.value.id, {
      name: editName.value.trim(),
      description: editDescription.value.trim() || null,
      item_category_id: selectedPart.value.item_category_id,
    })
    allParts.value = allParts.value.map((part) => (part.id === updated.id ? updated : part))
    showEditDialog.value = false
  } catch {
    editError.value = 'Could not save this item part. Please try again.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <UFormField label="Item part">
    <div class="flex gap-2">
      <InlineCreatableSelect
        v-model="partId"
        :options="availableParts"
        :loading="loading"
        :disabled="disabled || itemCategoryId === null"
        :create="createPart"
        placeholder="Select or type to add an item part"
      />
      <UButton
        v-if="selectedPart"
        icon="i-lucide-pencil"
        variant="ghost"
        aria-label="Edit item part"
        @click="openEditDialog"
      />
    </div>
  </UFormField>

  <UModal
    v-model:open="showEditDialog"
    title="Edit item part"
    :ui="{ content: 'max-w-md', footer: 'justify-end' }"
  >
    <template #body>
      <div class="flex flex-col gap-4">
        <UFormField label="Name">
          <UInput v-model="editName" class="w-full" autofocus />
        </UFormField>
        <UFormField label="Description" hint="Optional">
          <UTextarea v-model="editDescription" :rows="2" class="w-full" />
        </UFormField>
        <UAlert v-if="editError" color="error" variant="subtle" :description="editError" />
      </div>
    </template>
    <template #footer>
      <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="showEditDialog = false" />
      <UButton label="Save" icon="i-lucide-save" :loading="saving" @click="saveEdit" />
    </template>
  </UModal>
</template>
