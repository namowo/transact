<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import { FilterMatchMode } from '@openvue/core/api'
import { useConfirm } from '@/composables/useConfirm'
import ItemCategoryFields from '@/components/scenarios/ItemCategoryFields.vue'
import { itemCategoryApi, itemPartsCategoryApi, itemSubcategoryApi } from '@/api/categories'
import { createItem, deleteItem, listItems, updateItem } from '@/api/items'
import type { Item, ItemPartsCategory, ItemSubcategory, NamedCategory } from '@/api/types'
import type { TabsItem } from '@nuxt/ui'

const confirm = useConfirm()

// --- Categories ---
const categories = ref<NamedCategory[]>([])
const categoriesLoading = ref(false)
const categoriesFilter = ref('')

async function loadCategories() {
  categoriesLoading.value = true
  try {
    categories.value = await itemCategoryApi.list()
  } finally {
    categoriesLoading.value = false
  }
}

const filteredCategories = computed(() => {
  const query = categoriesFilter.value.trim().toLowerCase()
  if (!query) return categories.value
  return categories.value.filter((c) => (c.name ?? '').toLowerCase().includes(query))
})

// --- Subcategories ---
const subcategories = ref<ItemSubcategory[]>([])
const subcategoriesLoading = ref(false)

async function loadSubcategories() {
  subcategoriesLoading.value = true
  try {
    subcategories.value = await itemSubcategoryApi.list()
  } finally {
    subcategoriesLoading.value = false
  }
}

// --- Item parts ---
const parts = ref<ItemPartsCategory[]>([])
const partsLoading = ref(false)

async function loadParts() {
  partsLoading.value = true
  try {
    parts.value = await itemPartsCategoryApi.list()
  } finally {
    partsLoading.value = false
  }
}

// --- Items ---
const items = ref<Item[]>([])
const itemsLoading = ref(false)
const itemsLoadError = ref('')

async function loadItems() {
  itemsLoading.value = true
  itemsLoadError.value = ''
  try {
    items.value = await listItems()
  } catch {
    itemsLoadError.value = 'Could not load items.'
  } finally {
    itemsLoading.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadCategories(), loadSubcategories(), loadParts(), loadItems()])
  if (!selectedCategoryId.value) {
    selectedCategoryId.value = categories.value[0]?.id ?? null
  }
})

// --- Selected category (master list -> detail panel) ---
const selectedCategoryId = ref<string | null>(null)

const selectedCategory = computed(
  () => categories.value.find((c) => c.id === selectedCategoryId.value) ?? null,
)

const selectedCategorySubcategories = computed(() =>
  subcategories.value.filter((s) => s.item_category_id === selectedCategoryId.value),
)

const selectedCategoryParts = computed(() =>
  parts.value.filter((p) => p.item_category_id === selectedCategoryId.value),
)

function itemsForSubcategory(subcategoryId: string) {
  return items.value.filter((i) => i.item_subcategory_id === subcategoryId)
}

function selectCategory(id: string) {
  selectedCategoryId.value = id
}

// Expanded rows for the subcategory table: its description and nested
// items are shown in an expansion row rather than as their own columns.
const expandedSubcategoryRows = ref<Record<string, boolean>>({})

function initSubcategoryFilters() {
  return {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
    name: { value: null, matchMode: FilterMatchMode.CONTAINS },
  }
}

const subcategoryFilters = ref(initSubcategoryFilters())

function clearSubcategoryFilters() {
  subcategoryFilters.value = initSubcategoryFilters()
}

function initPartFilters() {
  return {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
    name: { value: null, matchMode: FilterMatchMode.CONTAINS },
    description: { value: null, matchMode: FilterMatchMode.CONTAINS },
  }
}

const partFilters = ref(initPartFilters())

function clearPartFilters() {
  partFilters.value = initPartFilters()
}

const categoryTabItems = computed<TabsItem[]>(() => [
  {
    label: 'Subcategories',
    value: 'subcategories',
    slot: 'subcategories',
    badge: selectedCategorySubcategories.value.length,
  },
  { label: 'Item parts', value: 'parts', slot: 'parts', badge: selectedCategoryParts.value.length },
])

// --- Shared name/description rename dialog (categories, subcategories, parts) ---
type RenameTarget = 'category' | 'subcategory' | 'part'

const renameDialogVisible = ref(false)
const renameTarget = ref<RenameTarget>('category')
const renameId = ref<string | null>(null)
const renameName = ref('')
const renameDescription = ref('')
const renameError = ref('')
const renameSaving = ref(false)

function openRenameDialog(target: RenameTarget, item: { id: string; name?: string | null; description?: string | null }) {
  renameTarget.value = target
  renameId.value = item.id
  renameName.value = item.name ?? ''
  renameDescription.value = item.description ?? ''
  renameError.value = ''
  renameDialogVisible.value = true
}

async function saveRename() {
  if (!renameId.value) return
  if (!renameName.value.trim()) {
    renameError.value = 'Name is required.'
    return
  }

  renameSaving.value = true
  renameError.value = ''
  try {
    const payload = { name: renameName.value.trim(), description: renameDescription.value.trim() || null }
    if (renameTarget.value === 'category') {
      const updated = await itemCategoryApi.update(renameId.value, payload)
      categories.value = categories.value.map((c) => (c.id === updated.id ? updated : c))
    } else if (renameTarget.value === 'subcategory') {
      const existing = subcategories.value.find((s) => s.id === renameId.value)
      const updated = await itemSubcategoryApi.update(renameId.value, {
        ...payload,
        item_category_id: existing?.item_category_id ?? null,
      })
      subcategories.value = subcategories.value.map((s) => (s.id === updated.id ? updated : s))
    } else {
      const existing = parts.value.find((p) => p.id === renameId.value)
      const updated = await itemPartsCategoryApi.update(renameId.value, {
        ...payload,
        item_category_id: existing?.item_category_id ?? null,
      })
      parts.value = parts.value.map((p) => (p.id === updated.id ? updated : p))
    }
    renameDialogVisible.value = false
  } catch {
    renameError.value = 'Could not save this change. Please try again.'
  } finally {
    renameSaving.value = false
  }
}

function confirmDeleteCategory(category: NamedCategory) {
  confirm.require({
    message: `Delete "${category.name}"? Subcategories, item parts, and items referencing it will be left uncategorized. This cannot be undone.`,
    header: 'Delete item category',
    rejectLabel: 'Cancel',
    acceptLabel: 'Delete',
    acceptColor: 'error',
    accept: async () => {
      await itemCategoryApi.delete(category.id)
      categories.value = categories.value.filter((c) => c.id !== category.id)
      if (selectedCategoryId.value === category.id) {
        selectedCategoryId.value = categories.value[0]?.id ?? null
      }
    },
  })
}

function confirmDeleteSubcategory(subcategory: ItemSubcategory) {
  confirm.require({
    message: `Delete "${subcategory.name}"? Items referencing it will be left without a subcategory. This cannot be undone.`,
    header: 'Delete item subcategory',
    rejectLabel: 'Cancel',
    acceptLabel: 'Delete',
    acceptColor: 'error',
    accept: async () => {
      await itemSubcategoryApi.delete(subcategory.id)
      subcategories.value = subcategories.value.filter((s) => s.id !== subcategory.id)
    },
  })
}

function confirmDeletePart(part: ItemPartsCategory) {
  confirm.require({
    message: `Delete "${part.name}"? Surface templates referencing it will be left without an item part. This cannot be undone.`,
    header: 'Delete item part',
    rejectLabel: 'Cancel',
    acceptLabel: 'Delete',
    acceptColor: 'error',
    accept: async () => {
      await itemPartsCategoryApi.delete(part.id)
      parts.value = parts.value.filter((p) => p.id !== part.id)
    },
  })
}

// --- Add category / subcategory / part dialogs ---
const addCategoryDialogVisible = ref(false)
const addCategoryName = ref('')
const addCategoryDescription = ref('')
const addCategoryError = ref('')
const addCategorySaving = ref(false)

function openAddCategoryDialog() {
  addCategoryName.value = ''
  addCategoryDescription.value = ''
  addCategoryError.value = ''
  addCategoryDialogVisible.value = true
}

async function saveAddCategory() {
  if (!addCategoryName.value.trim()) {
    addCategoryError.value = 'Name is required.'
    return
  }
  addCategorySaving.value = true
  addCategoryError.value = ''
  try {
    const created = await itemCategoryApi.create({
      name: addCategoryName.value.trim(),
      description: addCategoryDescription.value.trim() || null,
    })
    categories.value = [...categories.value, created]
    selectedCategoryId.value = created.id
    addCategoryDialogVisible.value = false
  } catch {
    addCategoryError.value = 'Could not add this category. Please try again.'
  } finally {
    addCategorySaving.value = false
  }
}

const addSubcategoryDialogVisible = ref(false)
const addSubcategoryName = ref('')
const addSubcategoryDescription = ref('')
const addSubcategoryError = ref('')
const addSubcategorySaving = ref(false)

function openAddSubcategoryDialog() {
  addSubcategoryName.value = ''
  addSubcategoryDescription.value = ''
  addSubcategoryError.value = ''
  addSubcategoryDialogVisible.value = true
}

async function saveAddSubcategory() {
  if (!selectedCategoryId.value) return
  if (!addSubcategoryName.value.trim()) {
    addSubcategoryError.value = 'Name is required.'
    return
  }
  addSubcategorySaving.value = true
  addSubcategoryError.value = ''
  try {
    const created = await itemSubcategoryApi.create({
      name: addSubcategoryName.value.trim(),
      description: addSubcategoryDescription.value.trim() || null,
      item_category_id: selectedCategoryId.value,
    })
    subcategories.value = [...subcategories.value, created]
    addSubcategoryDialogVisible.value = false
  } catch {
    addSubcategoryError.value = 'Could not add this subcategory. Please try again.'
  } finally {
    addSubcategorySaving.value = false
  }
}

const addPartDialogVisible = ref(false)
const addPartName = ref('')
const addPartDescription = ref('')
const addPartError = ref('')
const addPartSaving = ref(false)

function openAddPartDialog() {
  addPartName.value = ''
  addPartDescription.value = ''
  addPartError.value = ''
  addPartDialogVisible.value = true
}

async function saveAddPart() {
  if (!selectedCategoryId.value) return
  if (!addPartName.value.trim()) {
    addPartError.value = 'Name is required.'
    return
  }
  addPartSaving.value = true
  addPartError.value = ''
  try {
    const created = await itemPartsCategoryApi.create({
      name: addPartName.value.trim(),
      description: addPartDescription.value.trim() || null,
      item_category_id: selectedCategoryId.value,
    })
    parts.value = [...parts.value, created]
    addPartDialogVisible.value = false
  } catch {
    addPartError.value = 'Could not add this item part. Please try again.'
  } finally {
    addPartSaving.value = false
  }
}

// --- Items: edit / delete ---
interface ItemFormState {
  itemCategoryId: string | null
  itemSubcategoryId: string | null
  description: string
}

function emptyItemForm(item: Item | null, subcategoryId: string | null = null): ItemFormState {
  return {
    itemCategoryId: item?.item_category_id ?? selectedCategoryId.value,
    itemSubcategoryId: item?.item_subcategory_id ?? subcategoryId,
    description: item?.description ?? '',
  }
}

const itemSchema = yup.object({
  itemCategoryId: yup.string().nullable().required('Please select an item category.'),
  itemSubcategoryId: yup.string().nullable().required('Please select an item subcategory.'),
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

const [editItemCategoryId] = defineItemField('itemCategoryId')
const [editItemSubcategoryId] = defineItemField('itemSubcategoryId')
const [editItemDescription] = defineItemField('description')

const editItemDialogVisible = ref(false)
const editingItem = ref<Item | null>(null)
const editItemSaving = ref(false)
const editItemError = ref('')

function openAddItemDialog(subcategoryId: string) {
  editingItem.value = null
  resetItemForm({ values: emptyItemForm(null, subcategoryId) })
  editItemError.value = ''
  editItemDialogVisible.value = true
}

function openEditItemDialog(item: Item) {
  editingItem.value = item
  resetItemForm({ values: emptyItemForm(item) })
  editItemError.value = ''
  editItemDialogVisible.value = true
}

const saveEditItem = handleItemSubmit(async (values) => {
  editItemSaving.value = true
  editItemError.value = ''
  try {
    if (editingItem.value) {
      const updated = await updateItem(editingItem.value.id, {
        item_category_id: values.itemCategoryId,
        item_subcategory_id: values.itemSubcategoryId,
        description: values.description.trim(),
      })
      items.value = items.value.map((i) => (i.id === updated.id ? updated : i))
    } else {
      const created = await createItem({
        item_category_id: values.itemCategoryId,
        item_subcategory_id: values.itemSubcategoryId,
        description: values.description.trim(),
      })
      items.value = [...items.value, created]
    }
    editItemDialogVisible.value = false
  } catch {
    editItemError.value = 'Could not save this item. Please try again.'
  } finally {
    editItemSaving.value = false
  }
})

function confirmDeleteItem(item: Item) {
  confirm.require({
    message: `Delete this item (${item.description ?? 'no description'})? Surface templates referencing it will be left without an item. This cannot be undone.`,
    header: 'Delete item',
    rejectLabel: 'Cancel',
    acceptLabel: 'Delete',
    acceptColor: 'error',
    accept: async () => {
      await deleteItem(item.id)
      items.value = items.value.filter((i) => i.id !== item.id)
    },
  })
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Item Catalog</h1>

    <div class="flex flex-col gap-6 lg:flex-row lg:items-start">
      <!-- Master list: categories -->
      <div class="flex w-full flex-col gap-3 lg:w-72 lg:shrink-0">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold text-surface-900 dark:text-surface-0">Categories</h2>
          <UButton icon="i-lucide-plus" variant="ghost" size="sm" aria-label="Add category" @click="openAddCategoryDialog" />
        </div>
        <UInput
          v-model="categoriesFilter"
          type="text"
          icon="i-lucide-search"
          placeholder="Search categories"
        />
        <div class="flex flex-col overflow-hidden rounded-lg border border-surface-200 dark:border-surface-800">
          <template v-if="categoriesLoading">
            <div class="p-4 text-sm text-surface-500">Loading…</div>
          </template>
          <template v-else-if="filteredCategories.length === 0">
            <div class="p-4 text-sm text-surface-500">No item categories found.</div>
          </template>
          <button
            v-for="category in filteredCategories"
            :key="category.id"
            type="button"
            class="flex items-center justify-between gap-2 border-b border-surface-200 px-3 py-2.5 text-left text-sm last:border-b-0 dark:border-surface-800"
            :class="
              category.id === selectedCategoryId
                ? 'bg-primary-50 text-primary-700 dark:bg-primary-950 dark:text-primary-300'
                : 'text-surface-700 hover:bg-surface-50 dark:text-surface-300 dark:hover:bg-surface-900'
            "
            @click="selectCategory(category.id)"
          >
            <span class="truncate font-medium">{{ category.name ?? 'Unnamed' }}</span>
            <UIcon v-if="category.id === selectedCategoryId" name="i-lucide-chevron-right" class="shrink-0" />
          </button>
        </div>
      </div>

      <!-- Detail panel: selected category -->
      <div v-if="selectedCategory" class="flex min-w-0 flex-1 flex-col gap-6">
        <!-- Category header -->
        <div class="flex items-start justify-between gap-3 rounded-lg border border-surface-200 p-4 dark:border-surface-800">
          <div class="flex flex-col gap-1">
            <h2 class="text-lg font-semibold text-surface-900 dark:text-surface-0">
              {{ selectedCategory.name ?? 'Unnamed' }}
            </h2>
            <p class="text-sm text-surface-500">{{ selectedCategory.description ?? 'No description' }}</p>
          </div>
          <div class="flex shrink-0 gap-1">
            <UButton
              icon="i-lucide-pencil"
              variant="ghost"
              color="neutral"
              size="sm"
              aria-label="Edit category"
              @click="openRenameDialog('category', selectedCategory)"
            />
            <UButton
              icon="i-lucide-trash-2"
              variant="ghost"
              color="error"
              size="sm"
              aria-label="Delete category"
              @click="confirmDeleteCategory(selectedCategory)"
            />
          </div>
        </div>

        <!-- Subcategories / Item parts -->
        <UTabs default-value="subcategories" :items="categoryTabItems" class="w-full">
          <template #subcategories>
            <div class="flex flex-col gap-3">
              <div class="flex justify-end">
                <UButton label="Add subcategory" icon="i-lucide-plus" variant="soft" size="xs" @click="openAddSubcategoryDialog" />
              </div>
              <div class="mb-3 flex items-center justify-between gap-3">
                <UButton type="button" icon="i-lucide-filter-x" variant="outline" size="sm" @click="clearSubcategoryFilters()">
                  Clear Filters
                </UButton>
                <UInput
                  v-model="subcategoryFilters['global'].value"
                  type="text"
                  icon="i-lucide-search"
                  placeholder="Keyword Search"
                />
              </div>
              <div class="overflow-x-auto rounded-lg border border-surface-200 dark:border-surface-800">
                <DataTable
                  v-model:expanded-rows="expandedSubcategoryRows"
                  v-model:filters="subcategoryFilters"
                  :value="selectedCategorySubcategories"
                  :loading="subcategoriesLoading"
                  data-key="id"
                  filterDisplay="menu"
                  :globalFilterFields="['name']"
                >
                  <template #empty>No subcategories in this category yet.</template>
                  <Column expander style="width: 3rem" />
                  <Column
                    field="name"
                    header="Name"
                    sortable
                    :showFilterOperator="false"
                    :showAddButton="false"
                  >
                    <template #filter="{ filterModel }">
                      <UInput v-model="filterModel.value" type="text" placeholder="Search by name" />
                    </template>
                  </Column>
                  <Column header="" style="width: 6rem">
                    <template #body="{ data }">
                      <div class="flex justify-end gap-1">
                        <UButton
                          icon="i-lucide-pencil"
                          variant="ghost"
                          color="neutral"
                          size="sm"
                          aria-label="Edit subcategory"
                          @click="openRenameDialog('subcategory', data)"
                        />
                        <UButton
                          icon="i-lucide-trash-2"
                          variant="ghost"
                          color="error"
                          size="sm"
                          aria-label="Delete subcategory"
                          @click="confirmDeleteSubcategory(data)"
                        />
                      </div>
                    </template>
                  </Column>
                  <template #expansion="{ data }">
                    <div class="flex flex-col gap-4 px-4 py-3">
                      <div class="flex flex-col gap-1">
                        <h4 class="text-xs font-semibold uppercase tracking-wide text-surface-400">Description</h4>
                        <p class="text-sm text-surface-600 dark:text-surface-300">{{ data.description ?? 'No description' }}</p>
                      </div>

                      <div class="flex flex-col gap-2 border-t border-surface-200 pt-3 dark:border-surface-800">
                        <div class="flex items-center justify-between">
                          <h4 class="text-xs font-semibold uppercase tracking-wide text-surface-400">
                            Items in this subcategory
                          </h4>
                          <UButton
                            label="Add item"
                            icon="i-lucide-plus"
                            variant="soft"
                            size="xs"
                            @click="openAddItemDialog(data.id)"
                          />
                        </div>
                        <UAlert v-if="itemsLoadError" color="error" variant="outline" :description="itemsLoadError" />
                        <p v-else-if="itemsForSubcategory(data.id).length === 0" class="text-sm text-surface-500">
                          No items in this subcategory yet.
                        </p>
                        <ul v-else class="flex flex-col divide-y divide-surface-200 rounded-md border border-surface-200 dark:divide-surface-800 dark:border-surface-800">
                          <li
                            v-for="item in itemsForSubcategory(data.id)"
                            :key="item.id"
                            class="flex items-center justify-between gap-2 px-3 py-2 text-sm"
                          >
                            <span class="truncate">{{ item.description ?? '—' }}</span>
                            <div class="flex shrink-0 gap-1">
                              <UButton
                                icon="i-lucide-pencil"
                                variant="ghost"
                                color="neutral"
                                size="sm"
                                aria-label="Edit item"
                                @click="openEditItemDialog(item)"
                              />
                              <UButton
                                icon="i-lucide-trash-2"
                                variant="ghost"
                                color="error"
                                size="sm"
                                aria-label="Delete item"
                                @click="confirmDeleteItem(item)"
                              />
                            </div>
                          </li>
                        </ul>
                      </div>
                    </div>
                  </template>
                </DataTable>
              </div>
            </div>
          </template>

          <template #parts>
            <div class="flex flex-col gap-3">
              <div class="flex justify-end">
                <UButton label="Add item part" icon="i-lucide-plus" variant="soft" size="xs" @click="openAddPartDialog" />
              </div>
              <div class="mb-3 flex items-center justify-between gap-3">
                <UButton type="button" icon="i-lucide-filter-x" variant="outline" size="sm" @click="clearPartFilters()">
                  Clear Filters
                </UButton>
                <UInput
                  v-model="partFilters['global'].value"
                  type="text"
                  icon="i-lucide-search"
                  placeholder="Keyword Search"
                />
              </div>
              <div class="overflow-x-auto rounded-lg border border-surface-200 dark:border-surface-800">
                <DataTable
                  v-model:filters="partFilters"
                  :value="selectedCategoryParts"
                  :loading="partsLoading"
                  data-key="id"
                  filterDisplay="menu"
                  :globalFilterFields="['name', 'description']"
                >
                  <template #empty>No item parts in this category yet.</template>
                  <Column
                    field="name"
                    header="Name"
                    sortable
                    :showFilterOperator="false"
                    :showAddButton="false"
                  >
                    <template #filter="{ filterModel }">
                      <UInput v-model="filterModel.value" type="text" placeholder="Search by name" />
                    </template>
                  </Column>
                  <Column
                    field="description"
                    header="Description"
                    sortable
                    :showFilterOperator="false"
                    :showAddButton="false"
                  >
                    <template #body="{ data }">{{ data.description ?? '—' }}</template>
                    <template #filter="{ filterModel }">
                      <UInput v-model="filterModel.value" type="text" placeholder="Search by description" />
                    </template>
                  </Column>
                  <Column header="" style="width: 6rem">
                    <template #body="{ data }">
                      <div class="flex justify-end gap-1">
                        <UButton
                          icon="i-lucide-pencil"
                          variant="ghost"
                          color="neutral"
                          size="sm"
                          aria-label="Edit item part"
                          @click="openRenameDialog('part', data)"
                        />
                        <UButton
                          icon="i-lucide-trash-2"
                          variant="ghost"
                          color="error"
                          size="sm"
                          aria-label="Delete item part"
                          @click="confirmDeletePart(data)"
                        />
                      </div>
                    </template>
                  </Column>
                </DataTable>
              </div>
            </div>
          </template>
        </UTabs>
      </div>

      <div v-else class="flex flex-1 items-center justify-center rounded-lg border border-dashed border-surface-300 p-12 text-sm text-surface-500 dark:border-surface-700">
        Select a category, or add one, to see its subcategories and item parts.
      </div>
    </div>

    <!-- Shared rename dialog -->
    <UModal
      v-model:open="renameDialogVisible"
      :title="renameTarget === 'category' ? 'Edit category' : renameTarget === 'subcategory' ? 'Edit subcategory' : 'Edit item part'"
      :ui="{ content: 'max-w-md' }"
    >
      <template #body>
        <div class="flex flex-col gap-4">
          <UFormField label="Name">
            <UInput v-model="renameName" class="w-full" autofocus />
          </UFormField>
          <UFormField label="Description" hint="Optional">
            <UTextarea v-model="renameDescription" :rows="2" class="w-full" />
          </UFormField>
          <UAlert v-if="renameError" color="error" variant="subtle" :description="renameError" />
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" variant="ghost" @click="renameDialogVisible = false" />
        <UButton label="Save" :loading="renameSaving" @click="saveRename" />
      </template>
    </UModal>

    <!-- Add category dialog -->
    <UModal v-model:open="addCategoryDialogVisible" title="Add item category" :ui="{ content: 'max-w-md' }">
      <template #body>
        <div class="flex flex-col gap-4">
          <UFormField label="Name">
            <UInput v-model="addCategoryName" class="w-full" autofocus />
          </UFormField>
          <UFormField label="Description" hint="Optional">
            <UTextarea v-model="addCategoryDescription" :rows="2" class="w-full" />
          </UFormField>
          <UAlert v-if="addCategoryError" color="error" variant="subtle" :description="addCategoryError" />
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" variant="ghost" @click="addCategoryDialogVisible = false" />
        <UButton label="Add" :loading="addCategorySaving" @click="saveAddCategory" />
      </template>
    </UModal>

    <!-- Add subcategory dialog (always under the selected category) -->
    <UModal v-model:open="addSubcategoryDialogVisible" title="Add item subcategory" :ui="{ content: 'max-w-md' }">
      <template #body>
        <div class="flex flex-col gap-4">
          <p class="text-sm text-surface-500">
            Category: <span class="font-medium text-surface-700 dark:text-surface-300">{{ selectedCategory?.name ?? 'Unnamed' }}</span>
          </p>
          <UFormField label="Name">
            <UInput v-model="addSubcategoryName" class="w-full" autofocus />
          </UFormField>
          <UFormField label="Description" hint="Optional">
            <UTextarea v-model="addSubcategoryDescription" :rows="2" class="w-full" />
          </UFormField>
          <UAlert v-if="addSubcategoryError" color="error" variant="subtle" :description="addSubcategoryError" />
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" variant="ghost" @click="addSubcategoryDialogVisible = false" />
        <UButton label="Add" :loading="addSubcategorySaving" @click="saveAddSubcategory" />
      </template>
    </UModal>

    <!-- Add item part dialog (always under the selected category) -->
    <UModal v-model:open="addPartDialogVisible" title="Add item part" :ui="{ content: 'max-w-md' }">
      <template #body>
        <div class="flex flex-col gap-4">
          <p class="text-sm text-surface-500">
            Category: <span class="font-medium text-surface-700 dark:text-surface-300">{{ selectedCategory?.name ?? 'Unnamed' }}</span>
          </p>
          <UFormField label="Name">
            <UInput v-model="addPartName" class="w-full" autofocus />
          </UFormField>
          <UFormField label="Description" hint="Optional">
            <UTextarea v-model="addPartDescription" :rows="2" class="w-full" />
          </UFormField>
          <UAlert v-if="addPartError" color="error" variant="subtle" :description="addPartError" />
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" variant="ghost" @click="addPartDialogVisible = false" />
        <UButton label="Add" :loading="addPartSaving" @click="saveAddPart" />
      </template>
    </UModal>

    <!-- Add / edit item dialog -->
    <UModal v-model:open="editItemDialogVisible" :title="editingItem ? 'Edit item' : 'Add item'" :ui="{ content: 'max-w-md' }">
      <template #body>
        <div class="flex flex-col gap-4">
          <ItemCategoryFields
            v-model:category-id="editItemCategoryId"
            v-model:subcategory-id="editItemSubcategoryId"
            v-model:description="editItemDescription"
            :category-error="itemErrors.itemCategoryId"
            :subcategory-error="itemErrors.itemSubcategoryId"
            :description-error="itemErrors.description"
          />
          <UAlert v-if="editItemError" color="error" variant="subtle" :description="editItemError" />
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" variant="ghost" @click="editItemDialogVisible = false" />
        <UButton label="Save" :loading="editItemSaving" @click="saveEditItem" />
      </template>
    </UModal>
  </div>
</template>
