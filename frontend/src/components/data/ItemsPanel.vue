<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import ContextMenu from 'openvue/contextmenu'
import { FilterMatchMode } from '@openvue/core/api'
import DataTableSkeleton from '@/components/data/DataTableSkeleton.vue'
import ItemCategoryFields from '@/components/scenarios/ItemCategoryFields.vue'
import { useConfirm } from '@/composables/useConfirm'
import { createItem, deleteItem, listItems, updateItem } from '@/api/items'
import type { Item } from '@/api/types'
import type { MenuItem } from 'openvue/menuitem'

const confirm = useConfirm()

const items = ref<Item[]>([])
const loading = ref(false)
const loadError = ref('')

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    items.value = await listItems()
  } catch {
    loadError.value = 'Could not load items. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

function initItemFilters() {
  return {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
    'item_category.name': { value: null, matchMode: FilterMatchMode.CONTAINS },
    'item_subcategory.name': { value: null, matchMode: FilterMatchMode.CONTAINS },
    description: { value: null, matchMode: FilterMatchMode.CONTAINS },
  }
}

const itemFilters = ref(initItemFilters())

function clearItemFilters() {
  itemFilters.value = initItemFilters()
}

interface ItemFormState {
  itemCategoryId: string | null
  itemSubcategoryId: string | null
  description: string | null
}

function emptyItemForm(item: Item | null): ItemFormState {
  return {
    itemCategoryId: item?.item_category_id ?? null,
    itemSubcategoryId: item?.item_subcategory_id ?? null,
    description: item?.description ?? null,
  }
}

const itemSchema = yup.object({
  itemCategoryId: yup.string().nullable().required('Please select an item category.'),
  itemSubcategoryId: yup.string().nullable().defined(),
  description: yup.string().trim().required('Description is required.'),
})

const {
  defineField: defineItemField,
  errors: itemErrors,
  handleSubmit: handleItemSubmit,
  resetForm: resetItemForm,
} = useForm<ItemFormState>({
  validationSchema: itemSchema,
  initialValues: emptyItemForm(null),
})

const [itemCategoryId] = defineItemField('itemCategoryId')
const [itemSubcategoryId] = defineItemField('itemSubcategoryId')
const [itemDescription] = defineItemField('description')

const itemDialogVisible = ref(false)
const editingItemId = ref<string | null>(null)
const savingItem = ref(false)
const itemSaveError = ref('')

function openCreateItemDialog() {
  editingItemId.value = null
  resetItemForm({ values: emptyItemForm(null) })
  itemSaveError.value = ''
  itemDialogVisible.value = true
}

function openEditItemDialog(item: Item) {
  editingItemId.value = item.id
  resetItemForm({ values: emptyItemForm(item) })
  itemSaveError.value = ''
  itemDialogVisible.value = true
}

const saveItemForm = handleItemSubmit(async (values) => {
  savingItem.value = true
  itemSaveError.value = ''
  try {
    const payload = {
      item_category_id: values.itemCategoryId,
      item_subcategory_id: values.itemSubcategoryId,
      description: values.description?.trim() ?? null,
    }
    if (editingItemId.value === null) {
      const created = await createItem(payload)
      items.value = [...items.value, created]
    } else {
      const updated = await updateItem(editingItemId.value, payload)
      items.value = items.value.map((candidate) => (candidate.id === updated.id ? updated : candidate))
    }
    itemDialogVisible.value = false
  } catch {
    itemSaveError.value = 'Could not save this item. Please try again.'
  } finally {
    savingItem.value = false
  }
})

const deletingItem = ref(false)

function confirmDeleteItem(item: Item) {
  confirm.require({
    header: 'Delete item',
    message: 'Delete this item? This cannot be undone.',
    acceptLabel: 'Delete',
    acceptColor: 'error',
    rejectLabel: 'Cancel',
    accept: () => void removeItem(item),
  })
}

async function removeItem(item: Item) {
  deletingItem.value = true
  try {
    await deleteItem(item.id)
    items.value = items.value.filter((candidate) => candidate.id !== item.id)
  } finally {
    deletingItem.value = false
  }
}

// -- Context menu --

const contextMenu = ref<InstanceType<typeof ContextMenu>>()
const selectedItem = ref<Item>()

const contextMenuItems = computed<MenuItem[]>(() => {
  const item = selectedItem.value
  if (!item) return []
  return [
    {
      label: 'Edit',
      icon: 'i-lucide-pencil',
      command: () => openEditItemDialog(item),
    },
    {
      label: 'Delete',
      icon: 'i-lucide-trash-2',
      command: () => confirmDeleteItem(item),
    },
  ]
})

function onRowContextMenu(event: { originalEvent: Event; data: Item }) {
  selectedItem.value = event.data
  contextMenu.value?.show(event.originalEvent)
}

function openRowContextMenu(event: Event, item: Item) {
  selectedItem.value = item
  contextMenu.value?.show(event)
}

function onRowClick(event: { data: Item }) {
  openEditItemDialog(event.data)
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <UAlert v-if="loadError" color="error" variant="outline" :description="loadError" />

    <div class="flex items-center justify-between">
      <h4 class="font-medium">Items</h4>
      <UButton label="Add item" icon="i-lucide-plus" variant="outline" @click="openCreateItemDialog" />
    </div>
    <div class="overflow-x-auto">
      <div class="mb-3 flex items-center justify-between gap-3">
        <UButton
          type="button"
          icon="i-lucide-filter-x"
          variant="outline"
          size="sm"
          @click="clearItemFilters()"
        >
          Clear Filters
        </UButton>
        <UInput
          v-model="itemFilters['global'].value"
          type="text"
          icon="i-lucide-search"
          placeholder="Keyword Search"
        />
      </div>

      <ContextMenu ref="contextMenu" :model="contextMenuItems" />

      <DataTableSkeleton v-if="loading" :columns="4" />
      <DataTable
        v-else
        v-model:filters="itemFilters"
        v-model:context-menu-selection="selectedItem"
        :value="items"
        :loading="deletingItem"
        data-key="id"
        filterDisplay="menu"
        context-menu
        :globalFilterFields="['item_category.name', 'item_subcategory.name', 'description']"
        :row-class="() => 'cursor-pointer hover:bg-elevated'"
        @row-contextmenu="onRowContextMenu"
        @row-click="onRowClick"
      >
        <Column header="#" style="width: 3rem">
          <template #body="{ index }">{{ index + 1 }}</template>
        </Column>
        <Column
          field="item_category.name"
          header="Category"
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #body="{ data }">{{ data.item_category?.name ?? '—' }}</template>
          <template #filter="{ filterModel }">
            <UInput v-model="filterModel.value" type="text" placeholder="Search by category" />
          </template>
        </Column>
        <Column
          field="item_subcategory.name"
          header="Subcategory"
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #body="{ data }">{{ data.item_subcategory?.name ?? '—' }}</template>
          <template #filter="{ filterModel }">
            <UInput v-model="filterModel.value" type="text" placeholder="Search by subcategory" />
          </template>
        </Column>
        <Column
          field="description"
          header="Description"
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #filter="{ filterModel }">
            <UInput v-model="filterModel.value" type="text" placeholder="Search by description" />
          </template>
        </Column>
        <Column header="" style="width: 4rem">
          <template #body="{ data }">
            <UButton
              icon="i-lucide-more-vertical"
              color="neutral"
              variant="ghost"
              square
              aria-label="Item options"
              @click.stop="openRowContextMenu($event, data)"
            />
          </template>
        </Column>
      </DataTable>
    </div>

    <UModal
      v-model:open="itemDialogVisible"
      :title="editingItemId === null ? 'Add item' : 'Edit item'"
      :ui="{ content: 'max-w-md', footer: 'justify-end' }"
    >
      <template #body>
        <div class="flex flex-col gap-4">
          <ItemCategoryFields
            v-model:category-id="itemCategoryId"
            v-model:subcategory-id="itemSubcategoryId"
            v-model:description="itemDescription"
            :category-error="itemErrors.itemCategoryId"
            :description-error="itemErrors.description"
          />
          <UAlert v-if="itemSaveError" color="error" variant="outline" :description="itemSaveError" />
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="itemDialogVisible = false" />
        <UButton label="Save" icon="i-lucide-save" :loading="savingItem" @click="saveItemForm" />
      </template>
    </UModal>
  </div>
</template>
