<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import Select from 'primevue/select'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Textarea from 'primevue/textarea'
import CategorySelect from './CategorySelect.vue'
import { itemCategoryApi, itemSubcategoryApi } from '@/api/categories'
import { createItem, listItems, updateItem } from '@/api/items'
import type { Item } from '@/api/types'

// Selecting an item here just picks which Item row a surface points at;
// category, subcategory and description are edited entirely through this
// component's dialog too, so they aren't duplicated in SurfaceForm.
const itemId = defineModel<number | null>({ default: null })

const items = ref<Item[]>([])
const loading = ref(false)

// Items have no name of their own, so label them by creation order (not
// their database id, which is an implementation detail) plus whatever
// category is known, e.g. "Item 3 (Knife)".
function describeItem(item: Item): string {
  const position = items.value.findIndex((candidate) => candidate.id === item.id)
  const name = `Item ${position + 1}`
  return item.item_category?.name ? `${name} (${item.item_category.name})` : name
}

async function load() {
  loading.value = true
  try {
    items.value = (await listItems()).sort((a, b) => a.id - b.id)
  } finally {
    loading.value = false
  }
}

onMounted(load)

const selectedItem = computed(
  () => items.value.find((candidate) => candidate.id === itemId.value) ?? null,
)

interface FormState {
  itemCategoryId: number | null
  itemSubcategoryId: number | null
  description: string | null
}

function emptyForm(item: Item | null): FormState {
  return {
    itemCategoryId: item?.item_category_id ?? null,
    itemSubcategoryId: item?.item_subcategory_id ?? null,
    description: item?.description ?? null,
  }
}

const schema = yup.object({
  itemCategoryId: yup.number().nullable().defined(),
  itemSubcategoryId: yup.number().nullable().defined(),
  description: yup.string().nullable().defined(),
})

const { defineField, handleSubmit, resetForm: resetFormValues } = useForm<FormState>({
  validationSchema: schema,
  initialValues: emptyForm(null),
})

const [formItemCategoryId] = defineField('itemCategoryId')
const [formItemSubcategoryId] = defineField('itemSubcategoryId')
const [formDescription] = defineField('description')

const showDialog = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const saving = ref(false)
const saveError = ref('')

function openCreateDialog() {
  dialogMode.value = 'create'
  resetFormValues({ values: emptyForm(null) })
  saveError.value = ''
  showDialog.value = true
}

function openEditDialog() {
  if (!selectedItem.value) return
  dialogMode.value = 'edit'
  resetFormValues({ values: emptyForm(selectedItem.value) })
  saveError.value = ''
  showDialog.value = true
}

const saveItem = handleSubmit(async (values) => {
  saving.value = true
  saveError.value = ''
  try {
    const payload = {
      item_category_id: values.itemCategoryId,
      item_subcategory_id: values.itemSubcategoryId,
      description: values.description,
    }
    if (dialogMode.value === 'edit' && selectedItem.value) {
      const updated = await updateItem(selectedItem.value.id, payload)
      items.value = items.value.map((candidate) =>
        candidate.id === updated.id ? updated : candidate,
      )
    } else {
      const created = await createItem(payload)
      items.value = [...items.value, created]
      itemId.value = created.id
    }
    showDialog.value = false
  } catch {
    saveError.value = 'Could not save this item. Please try again.'
  } finally {
    saving.value = false
  }
})
</script>

<template>
  <div class="flex flex-col gap-2">
    <label class="font-medium text-sm">Item</label>
    <div class="flex gap-2">
      <Select
        v-model="itemId"
        :options="items"
        :option-label="describeItem"
        option-value="id"
        placeholder="Select an item"
        :loading="loading"
        show-clear
        filter
        fluid
      />
      <Button
        v-if="selectedItem"
        icon="pi pi-pencil"
        text
        aria-label="Edit item"
        @click="openEditDialog"
      />
      <Button icon="pi pi-plus" text aria-label="Add new item" @click="openCreateDialog" />
    </div>

    <Dialog
      v-model:visible="showDialog"
      :header="dialogMode === 'edit' ? 'Edit item' : 'Add item'"
      modal
      :style="{ width: '28rem' }"
    >
      <div class="flex flex-col gap-4">
        <CategorySelect v-model="formItemCategoryId" label="Item category" :api="itemCategoryApi" />
        <CategorySelect
          v-model="formItemSubcategoryId"
          label="Item subcategory"
          :api="itemSubcategoryApi"
        />
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Description (Optional)</label>
          <Textarea v-model="formDescription" rows="2" fluid />
        </div>
        <p v-if="saveError" class="text-sm text-red-500">{{ saveError }}</p>
      </div>
      <template #footer>
        <Button label="Cancel" text @click="showDialog = false" />
        <Button label="Save" :loading="saving" @click="saveItem" />
      </template>
    </Dialog>
  </div>
</template>
