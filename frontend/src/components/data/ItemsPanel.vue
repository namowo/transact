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
import type { ContactTemplate, Item } from '@/api/types'
import type { MenuItem } from 'openvue/menuitem'

const props = defineProps<{ studyId: string; contactTemplates?: ContactTemplate[] }>()

const confirm = useConfirm()

// Items are a shared catalog - this tab only shows the items this study has
// explicitly added to itself, not every item in the whole catalog.
const allItems = ref<Item[]>([])
const items = computed(() =>
  allItems.value.filter((item) => item.studies?.some((study) => study.id === props.studyId)),
)
const loading = ref(false)
const loadError = ref('')

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    allItems.value = await listItems()
  } catch {
    loadError.value = 'Could not load items. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

function replaceItem(updated: Item) {
  allItems.value = allItems.value.map((candidate) => (candidate.id === updated.id ? updated : candidate))
}

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
  quantity: number
}

function emptyItemForm(item: Item | null): ItemFormState {
  return {
    itemCategoryId: item?.item_category_id ?? null,
    itemSubcategoryId: item?.item_subcategory_id ?? null,
    description: item?.description ?? null,
    quantity: 1,
  }
}

const itemSchema = yup.object({
  itemCategoryId: yup.string().nullable().required('Please select an item category.'),
  itemSubcategoryId: yup.string().nullable().defined(),
  description: yup.string().trim().required('Description is required.'),
  quantity: yup.number().min(1, 'Quantity must be at least 1.').required(),
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
const [itemQuantity] = defineItemField('quantity')

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
      const created = await Promise.all(
        Array.from({ length: values.quantity }, () =>
          createItem({ ...payload, study_ids: [props.studyId] }),
        ),
      )
      allItems.value = [...allItems.value, ...created]
    } else {
      const updated = await updateItem(editingItemId.value, payload)
      replaceItem(updated)
    }
    itemDialogVisible.value = false
  } catch {
    itemSaveError.value = 'Could not save this item. Please try again.'
  } finally {
    savingItem.value = false
  }
})

const deletingItem = ref(false)

// An item still used by other studies is only unlinked from this one; it's
// hard-deleted from the shared catalog only once this was its last study.
function itemUsedByOtherStudies(item: Item): boolean {
  return (item.studies ?? []).some((study) => study.id !== props.studyId)
}

function confirmDeleteItem(item: Item) {
  const usedElsewhere = itemUsedByOtherStudies(item)
  confirm.require({
    header: usedElsewhere ? 'Remove item from study' : 'Delete item',
    message: usedElsewhere
      ? 'Remove this item from this study? It will stay available in the other studies using it.'
      : 'Delete this item? This cannot be undone.',
    acceptLabel: usedElsewhere ? 'Remove' : 'Delete',
    acceptColor: 'error',
    rejectLabel: 'Cancel',
    accept: () => void removeItem(item),
  })
}

async function removeItem(item: Item) {
  deletingItem.value = true
  try {
    if (itemUsedByOtherStudies(item)) {
      const remainingStudyIds = (item.studies ?? [])
        .map((study) => study.id)
        .filter((id) => id !== props.studyId)
      const updated = await updateItem(item.id, { study_ids: remainingStudyIds })
      replaceItem(updated)
    } else {
      await deleteItem(item.id)
      allItems.value = allItems.value.filter((candidate) => candidate.id !== item.id)
    }
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
      label: itemUsedByOtherStudies(item) ? 'Remove from study' : 'Delete',
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

// -- Add existing item (from the shared catalog) --

const pickerVisible = ref(false)
const addingExistingItem = ref(false)

const catalogItemsNotInStudy = computed(() =>
  allItems.value.filter((item) => !item.studies?.some((study) => study.id === props.studyId)),
)

function describeCatalogItem(item: Item): string {
  return (
    [item.item_category?.name, item.item_subcategory?.name].filter(Boolean).join(' — ') ||
    'Uncategorized'
  )
}

function initPickerFilters() {
  return {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
  }
}

const pickerFilters = ref(initPickerFilters())

async function addExistingItem(item: Item) {
  addingExistingItem.value = true
  try {
    const studyIds = [...(item.studies ?? []).map((study) => study.id), props.studyId]
    const updated = await updateItem(item.id, { study_ids: studyIds })
    replaceItem(updated)
    pickerVisible.value = false
  } finally {
    addingExistingItem.value = false
  }
}

function openPicker() {
  pickerFilters.value = initPickerFilters()
  pickerVisible.value = true
}

// Jumps from "no match in the catalog" straight into creating one, instead
// of making the user close the picker and reopen the separate create
// dialog - the catalog is shared across studies (as used elsewhere, e.g.
// contact templates), so most of the time the item already exists.
function openCreateItemDialogFromPicker() {
  pickerVisible.value = false
  openCreateItemDialog()
}

// -- Load items referenced by this study's planned scenario templates --
// A contact template's donor/recipient slot can point at an Item (planned
// during scenario setup), but instantiating that template into an actual
// Contact doesn't itself add the item to this study's item list - so items
// used in planning can be invisible here even though they're in use. This
// surfaces them in one step instead of requiring each to be found and
// added one by one through the picker.

function templateItemIds(templates: ContactTemplate[]): Set<string> {
  const ids = new Set<string>()
  for (const template of templates) {
    const donorId = template.donor_surface_template?.item_id
    const recipientId = template.recipient_surface_template?.item_id
    if (donorId) ids.add(donorId)
    if (recipientId) ids.add(recipientId)
  }
  return ids
}

const itemsFromTemplatesNotInStudy = computed(() => {
  const ids = templateItemIds(props.contactTemplates ?? [])
  return allItems.value.filter(
    (item) => ids.has(item.id) && !item.studies?.some((study) => study.id === props.studyId),
  )
})

const loadingTemplateItems = ref(false)

async function loadItemsFromTemplates() {
  loadingTemplateItems.value = true
  try {
    for (const item of itemsFromTemplatesNotInStudy.value) {
      const studyIds = [...(item.studies ?? []).map((study) => study.id), props.studyId]
      const updated = await updateItem(item.id, { study_ids: studyIds })
      replaceItem(updated)
    }
  } finally {
    loadingTemplateItems.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <UAlert v-if="loadError" color="error" variant="outline" :description="loadError" />

    <div v-if="loading || items.length" class="flex items-center justify-between">
      <h4 class="font-medium">Items</h4>
      <div class="flex gap-2">
        <UButton
          v-if="itemsFromTemplatesNotInStudy.length"
          :label="`Load ${itemsFromTemplatesNotInStudy.length} item${itemsFromTemplatesNotInStudy.length === 1 ? '' : 's'} from scenario templates`"
          icon="i-lucide-download"
          variant="outline"
          :loading="loadingTemplateItems"
          @click="loadItemsFromTemplates"
        />
        <UButton label="Add item" icon="i-lucide-search" variant="outline" @click="openPicker" />
      </div>
    </div>

    <DataTableSkeleton v-if="loading" :columns="4" />

    <div v-else-if="!items.length" class="flex flex-col items-center gap-3 py-16">
      <h4 class="font-medium">Items</h4>
      <p class="text-sm text-surface-500 dark:text-surface-400">No items added to this study yet.</p>
      <div class="flex gap-2">
        <UButton
          v-if="itemsFromTemplatesNotInStudy.length"
          :label="`Load ${itemsFromTemplatesNotInStudy.length} item${itemsFromTemplatesNotInStudy.length === 1 ? '' : 's'} from scenario templates`"
          icon="i-lucide-download"
          variant="outline"
          :loading="loadingTemplateItems"
          @click="loadItemsFromTemplates"
        />
        <UButton label="Add item" icon="i-lucide-search" variant="outline" @click="openPicker" />
      </div>
    </div>

    <div v-else class="overflow-x-auto">
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

      <DataTable
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
          <UFormField
            v-if="editingItemId === null"
            label="Quantity"
            hint="Creates this many identical, separate items"
            :error="itemErrors.quantity"
          >
            <UInputNumber v-model="itemQuantity" :min="1" class="w-full" />
          </UFormField>
          <UAlert v-if="itemSaveError" color="error" variant="outline" :description="itemSaveError" />
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="itemDialogVisible = false" />
        <UButton
          :label="editingItemId === null && itemQuantity > 1 ? `Save ${itemQuantity} items` : 'Save'"
          icon="i-lucide-save"
          :loading="savingItem"
          @click="saveItemForm"
        />
      </template>
    </UModal>

    <UModal
      v-model:open="pickerVisible"
      title="Add item"
      :ui="{ content: 'max-w-3xl', footer: 'justify-end' }"
    >
      <template #body>
        <div class="flex flex-col gap-3">
          <UInput
            v-model="pickerFilters['global'].value"
            type="text"
            icon="i-lucide-search"
            placeholder="Search the item catalog"
            class="w-full"
          />

          <DataTable
            v-model:filters="pickerFilters"
            :value="catalogItemsNotInStudy"
            :globalFilterFields="['item_category.name', 'item_subcategory.name', 'description']"
            dataKey="id"
            scrollable
            scrollHeight="28rem"
            :loading="addingExistingItem"
            :row-class="() => 'cursor-pointer hover:bg-elevated'"
            @row-click="({ data }) => addExistingItem(data)"
          >
            <template #empty>
              <div class="flex flex-col items-center gap-2 py-4">
                <p class="text-sm text-surface-500 dark:text-surface-400">No matching item in the catalog.</p>
                <UButton
                  label="Create new item"
                  icon="i-lucide-plus"
                  variant="outline"
                  size="sm"
                  @click="openCreateItemDialogFromPicker"
                />
              </div>
            </template>
            <Column header="Item">
              <template #body="{ data }">{{ describeCatalogItem(data) }}</template>
            </Column>
            <Column field="description" header="Description" />
          </DataTable>
        </div>
      </template>
      <template #footer>
        <UButton
          label="Create new item"
          icon="i-lucide-plus"
          variant="outline"
          @click="openCreateItemDialogFromPicker"
        />
        <UButton label="Close" icon="i-lucide-x" variant="ghost" @click="pickerVisible = false" />
      </template>
    </UModal>
  </div>
</template>
