<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import ItemCategoryFields from './ItemCategoryFields.vue'
import { createItem, listItemsGrouped, updateItem } from '@/api/items'
import type { Item, ItemGroup } from '@/api/types'

// Selecting an item here just picks which Item row a surface points at;
// category, subcategory and description are edited entirely through this
// component's dialog too, so they aren't duplicated in SurfaceForm.
const itemId = defineModel<string | null>({ default: null })

// Exposes the selected item's category so a parent form (SurfaceTemplateForm)
// can scope an item-part picker to it, without storing the category on the
// draft itself - it's derived from the item, not persisted independently.
const itemCategoryId = defineModel<string | null>('itemCategoryId', { default: null })

const groups = ref<ItemGroup[]>([])
const loading = ref(false)

const items = computed(() => groups.value.flatMap((group) => group.items))

async function load() {
  loading.value = true
  try {
    groups.value = await listItemsGrouped()
  } finally {
    loading.value = false
  }
}

onMounted(load)

const selectedItem = computed(
  () => items.value.find((candidate) => candidate.id === itemId.value) ?? null,
)

watch(
  selectedItem,
  (item) => {
    itemCategoryId.value = item?.item_category_id ?? null
  },
  { immediate: true },
)

function describeItem(item: Item): string {
  return [item.item_category?.name, item.item_subcategory?.name].filter(Boolean).join(' — ') || 'Uncategorized'
}

// Items are only distinguished by category/subcategory/description (they
// have no name of their own), and two items can legitimately share all of
// those - so picking from a flat dropdown risks indistinguishable duplicate
// labels. A filterable table makes every row's full detail visible instead.
const pickerVisible = ref(false)
const pickerFilter = ref('')

interface FormState {
  itemCategoryId: string | null
  itemSubcategoryId: string | null
  description: string
}

function emptyForm(item: Item | null): FormState {
  return {
    itemCategoryId: item?.item_category_id ?? null,
    itemSubcategoryId: item?.item_subcategory_id ?? null,
    description: item?.description ?? '',
  }
}

const schema = yup.object({
  itemCategoryId: yup.string().nullable().required('Please select an item category.'),
  itemSubcategoryId: yup.string().nullable().defined(),
  description: yup.string().trim().required('Description is required.'),
})

const { defineField, errors, handleSubmit, resetForm: resetFormValues } = useForm<FormState>({
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
      description: values.description.trim(),
    }
    if (dialogMode.value === 'edit' && selectedItem.value) {
      await updateItem(selectedItem.value.id, payload)
      await load()
    } else {
      const created = await createItem(payload)
      await load()
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
    <UFormField label="Item">
      <div class="flex gap-2">
        <UButton
          :label="selectedItem ? describeItem(selectedItem) : 'Select an item'"
          icon="i-lucide-search"
          color="neutral"
          variant="outline"
          :loading="loading"
          class="w-full justify-start"
          :ui="{ base: 'truncate' }"
          :title="selectedItem?.description ?? undefined"
          @click="pickerVisible = true"
        />
        <UButton
          v-if="itemId"
          icon="i-lucide-x"
          variant="ghost"
          aria-label="Clear item"
          @click="itemId = null"
        />
        <UButton
          v-if="selectedItem"
          icon="i-lucide-pencil"
          variant="ghost"
          aria-label="Edit item"
          @click="openEditDialog"
        />
        <UButton icon="i-lucide-plus" variant="ghost" aria-label="Add new item" @click="openCreateDialog" />
      </div>
    </UFormField>

    <UModal
      v-model:open="pickerVisible"
      title="Select an item"
      :ui="{ content: 'max-w-3xl' }"
    >
      <template #body>
        <div class="flex flex-col gap-3">
          <UInput
            v-model="pickerFilter"
            type="text"
            icon="i-lucide-search"
            placeholder="Search items"
            class="w-full"
          />

          <DataTable
            :value="items"
            :globalFilterFields="['item_category.name', 'item_subcategory.name', 'description']"
            :filters="{ global: { value: pickerFilter, matchMode: 'contains' } }"
            dataKey="id"
            scrollable
            scrollHeight="28rem"
            selectionMode="single"
            :metaKeySelection="false"
            @row-click="({ data }) => { itemId = data.id; pickerVisible = false }"
          >
            <template #empty>No items found.</template>
            <Column field="item_category.name" header="Category">
              <template #body="{ data }">{{ data.item_category?.name ?? 'Uncategorized' }}</template>
            </Column>
            <Column field="item_subcategory.name" header="Subcategory">
              <template #body="{ data }">{{ data.item_subcategory?.name ?? '—' }}</template>
            </Column>
            <Column field="description" header="Description" />
          </DataTable>
        </div>
      </template>
      <template #footer>
        <UButton label="Close" variant="ghost" @click="pickerVisible = false" />
      </template>
    </UModal>

    <UModal
      v-model:open="showDialog"
      :title="dialogMode === 'edit' ? 'Edit item' : 'Add item'"
      :ui="{ content: 'max-w-md' }"
    >
      <template #body>
        <div class="flex flex-col gap-4">
          <ItemCategoryFields
            v-model:category-id="formItemCategoryId"
            v-model:subcategory-id="formItemSubcategoryId"
            v-model:description="formDescription"
            :category-error="errors.itemCategoryId"
            :description-error="errors.description"
          />
          <p v-if="saveError" class="text-sm text-red-500">{{ saveError }}</p>
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" variant="ghost" @click="showDialog = false" />
        <UButton label="Save" :loading="saving" @click="saveItem" />
      </template>
    </UModal>
  </div>
</template>
