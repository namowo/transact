<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import DataTableSkeleton from '@/components/data/DataTableSkeleton.vue'
import ItemCategoryFields from '@/components/scenarios/ItemCategoryFields.vue'
import { useConfirm } from '@/composables/useConfirm'
import { useStudyReadOnly } from '@/composables/useStudyAccess'
import { createItem, deleteItem, listItems, updateItem } from '@/api/items'
import ScenarioBadges from '@/components/data/ScenarioBadges.vue'
import ScenarioMultiSelect from '@/components/data/ScenarioMultiSelect.vue'
import type { ContactTemplate, Item, Scenario } from '@/api/types'
import type { ContextMenuItem, TableColumn, TableRow } from '@nuxt/ui'
import { manualSorting, searchRows, useTableView } from '@/composables/useTableView'
import { sortHeader } from '@/composables/tableColumns'
import TableFilterDrawer from '@/components/ui/TableFilterDrawer.vue'

const props = defineProps<{
  studyId: string
  contactTemplates?: ContactTemplate[]
  scenarios: Scenario[]
  scenarioId: string | null
}>()
const emit = defineEmits<{ 'update:count': [count: number] }>()

const confirm = useConfirm()
const readOnly = useStudyReadOnly()

// Items are a shared catalog - this tab only shows the items this study has
// explicitly added to itself, not every item in the whole catalog. Within
// the study, every item is assigned to at least one of its scenarios.
const allItems = ref<Item[]>([])
const items = computed(() =>
  allItems.value.filter(
    (item) =>
      item.studies?.some((study) => study.id === props.studyId) &&
      (props.scenarioId === null || !!item.scenario_ids?.includes(props.scenarioId)),
  ),
)

const studyScenarioIds = computed(() => new Set(props.scenarios.map((scenario) => scenario.id)))

// An item's scenario links, split into this study's and other studies'
// scenarios - editing here only changes the former.
function studyScenarioIdsOf(item: Item): string[] {
  return (item.scenario_ids ?? []).filter((id) => studyScenarioIds.value.has(id))
}

function otherScenarioIdsOf(item: Item): string[] {
  return (item.scenario_ids ?? []).filter((id) => !studyScenarioIds.value.has(id))
}

const scenarioRequiredMessage = 'Select at least one scenario.'
watch(
  () => items.value.length,
  (count) => emit('update:count', count),
  { immediate: true },
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
  allItems.value = allItems.value.map((candidate) =>
    candidate.id === updated.id ? updated : candidate,
  )
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

const itemScenarioIds = ref<string[]>([])
const itemScenarioError = ref('')

watch(itemScenarioIds, (ids) => {
  if (ids.length) itemScenarioError.value = ''
})

function openCreateItemDialog(scenarioIds?: string[]) {
  editingItemId.value = null
  itemScenarioIds.value = scenarioIds?.length
    ? [...scenarioIds]
    : props.scenarioId
      ? [props.scenarioId]
      : []
  itemScenarioError.value = ''
  resetItemForm({ values: emptyItemForm(null) })
  itemSaveError.value = ''
  itemDialogVisible.value = true
}

function openEditItemDialog(item: Item) {
  editingItemId.value = item.id
  itemScenarioIds.value = studyScenarioIdsOf(item)
  itemScenarioError.value = ''
  resetItemForm({ values: emptyItemForm(item) })
  itemSaveError.value = ''
  itemDialogVisible.value = true
}

function saveItemForm() {
  itemScenarioError.value = itemScenarioIds.value.length ? '' : scenarioRequiredMessage
  void submitItemForm()
}

const submitItemForm = handleItemSubmit(async (values) => {
  if (itemScenarioError.value) return
  savingItem.value = true
  itemSaveError.value = ''
  const editedItem = allItems.value.find((item) => item.id === editingItemId.value)
  try {
    const payload = {
      item_category_id: values.itemCategoryId,
      item_subcategory_id: values.itemSubcategoryId,
      description: values.description?.trim() ?? null,
      scenario_ids: [
        ...(editedItem ? otherScenarioIdsOf(editedItem) : []),
        ...itemScenarioIds.value,
      ],
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

function menuItems(item: Item): ContextMenuItem[] {
  return [
    {
      label: 'Edit',
      icon: 'i-lucide-pencil',
      onSelect: () => openEditItemDialog(item),
    },
    {
      label: itemUsedByOtherStudies(item) ? 'Remove from study' : 'Delete',
      icon: 'i-lucide-trash-2',
      color: 'error',
      onSelect: () => confirmDeleteItem(item),
    },
  ]
}

// The right-clicked row's menu.
const contextMenuItems = ref<ContextMenuItem[]>([])

function onRowContextMenu(_event: Event, row: TableRow<ItemRow>) {
  contextMenuItems.value = readOnly.value ? [] : menuItems(row.original)
}

function onRowSelect(_event: Event, row: TableRow<ItemRow>) {
  if (readOnly.value) return
  openEditItemDialog(row.original)
}

function itemScenarioNames(item: Item): string[] {
  return props.scenarios.filter((s) => item.scenario_ids?.includes(s.id)).map((s) => s.name)
}

type ItemRow = Item & { scenarioNames: string }

const itemRows = computed<ItemRow[]>(() =>
  items.value.map((item) => ({ ...item, scenarioNames: itemScenarioNames(item).join(', ') })),
)

const view = useTableView(itemRows, {
  searchFields: ['item_category.name', 'item_subcategory.name', 'description', 'scenarioNames'],
  filters: {
    category: { field: 'item_category.name' },
    subcategory: { field: 'item_subcategory.name' },
    description: { field: 'description' },
    scenario: { field: 'scenarioNames' },
  },
  sortAccessors: { category: 'item_category.name', subcategory: 'item_subcategory.name' },
})

const columns = computed<TableColumn<ItemRow>[]>(() => [
  { id: 'index', header: '#', meta: { class: { td: 'w-12' } } },
  { id: 'category', header: sortHeader('Category') },
  { id: 'subcategory', header: sortHeader('Subcategory') },
  { id: 'description', accessorKey: 'description', header: sortHeader('Description') },
  { id: 'scenarioNames', accessorKey: 'scenarioNames', header: sortHeader('Scenario') },
  ...(readOnly.value ? [] : [{ id: 'actions', header: '', meta: { class: { td: 'w-16' } } }]),
])

// -- Add existing item (from the shared catalog) --

const pickerVisible = ref(false)
const addingExistingItem = ref(false)

// Items not yet part of the current view: not in the study at all, or in
// the study but not used in the selected scenario.
const catalogItemsNotInStudy = computed(() => {
  const visible = new Set(items.value.map((item) => item.id))
  return allItems.value.filter((item) => !visible.has(item.id))
})

// Study + scenario links that add an existing item to this study's
// `scenarioIds`, keeping its other links.
function linksAddingScenarios(item: Item, scenarioIds: string[]) {
  const studyIds = new Set((item.studies ?? []).map((study) => study.id))
  studyIds.add(props.studyId)
  return {
    study_ids: [...studyIds],
    scenario_ids: [...new Set([...(item.scenario_ids ?? []), ...scenarioIds])],
  }
}

function describeCatalogItem(item: Item): string {
  return (
    [item.item_category?.name, item.item_subcategory?.name].filter(Boolean).join(' — ') ||
    'Uncategorized'
  )
}

const pickerSearch = ref('')
const visibleCatalogItems = computed(() =>
  searchRows(
    catalogItemsNotInStudy.value,
    ['item_category.name', 'item_subcategory.name', 'description'],
    pickerSearch.value,
  ),
)
const pickerColumns: TableColumn<Item>[] = [
  { id: 'item', header: 'Item' },
  { id: 'description', accessorKey: 'description', header: 'Description' },
]

const pickerScenarioIds = ref<string[]>([])
const pickerScenarioError = ref('')

watch(pickerScenarioIds, (ids) => {
  if (ids.length) pickerScenarioError.value = ''
})

async function addExistingItem(item: Item) {
  if (!pickerScenarioIds.value.length) {
    pickerScenarioError.value = scenarioRequiredMessage
    return
  }
  addingExistingItem.value = true
  try {
    const updated = await updateItem(item.id, linksAddingScenarios(item, pickerScenarioIds.value))
    replaceItem(updated)
    pickerVisible.value = false
  } finally {
    addingExistingItem.value = false
  }
}

function openPicker() {
  pickerSearch.value = ''
  pickerScenarioIds.value = props.scenarioId ? [props.scenarioId] : []
  pickerScenarioError.value = ''
  pickerVisible.value = true
}

// Jumps from "no match in the catalog" straight into creating one, instead
// of making the user close the picker and reopen the separate create
// dialog - the catalog is shared across studies (as used elsewhere, e.g.
// contact templates), so most of the time the item already exists.
function openCreateItemDialogFromPicker() {
  pickerVisible.value = false
  openCreateItemDialog(pickerScenarioIds.value)
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
  const visible = new Set(items.value.map((item) => item.id))
  return allItems.value.filter((item) => ids.has(item.id) && !visible.has(item.id))
})

const loadingTemplateItems = ref(false)

// The scenarios (in the current view) whose planned templates use the item.
function scenariosUsingItem(item: Item): string[] {
  const ids = props.scenarios
    .filter((scenario) => props.scenarioId === null || scenario.id === props.scenarioId)
    .filter((scenario) => templateItemIds(scenario.contact_templates).has(item.id))
    .map((scenario) => scenario.id)
  return ids.length || !props.scenarioId ? ids : [props.scenarioId]
}

async function loadItemsFromTemplates() {
  loadingTemplateItems.value = true
  try {
    for (const item of itemsFromTemplatesNotInStudy.value) {
      const scenarioIds = scenariosUsingItem(item)
      if (!scenarioIds.length) continue
      const updated = await updateItem(item.id, linksAddingScenarios(item, scenarioIds))
      replaceItem(updated)
    }
  } finally {
    loadingTemplateItems.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-4" data-tour="items-panel">
    <UAlert v-if="loadError" color="error" variant="outline" :description="loadError" />

    <div v-if="loading || items.length" class="flex items-center justify-between">
      <h4 class="font-medium">Items</h4>
      <div v-if="!readOnly" class="flex gap-2" data-tour="items-actions">
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
      <p class="text-sm text-surface-500 dark:text-surface-400">
        No items added to this study yet.
      </p>
      <div v-if="!readOnly" class="flex gap-2" data-tour="items-actions">
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

    <div v-else class="flex flex-col gap-3">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <UInput
          v-model="view.search"
          icon="i-lucide-search"
          placeholder="Keyword Search"
          class="w-full max-w-sm"
        />
        <TableFilterDrawer :active-count="view.activeFilterCount" @reset="view.resetFilters()">
          <UFormField label="Category">
            <UInput
              v-model="view.filters.category"
              placeholder="Search by category"
              class="w-full"
            />
          </UFormField>
          <UFormField label="Subcategory">
            <UInput
              v-model="view.filters.subcategory"
              placeholder="Search by subcategory"
              class="w-full"
            />
          </UFormField>
          <UFormField label="Description">
            <UInput
              v-model="view.filters.description"
              placeholder="Search by description"
              class="w-full"
            />
          </UFormField>
          <UFormField label="Scenario">
            <UInput
              v-model="view.filters.scenario"
              placeholder="Search by scenario"
              class="w-full"
            />
          </UFormField>
        </TableFilterDrawer>
      </div>

      <UContextMenu :items="contextMenuItems" :disabled="readOnly">
        <UTable
          v-model:sorting="view.sorting"
          :sorting-options="manualSorting"
          :data="view.rows"
          :columns="columns"
          :loading="deletingItem"
          :get-row-id="(item: ItemRow) => item.id"
          :on-select="readOnly ? undefined : onRowSelect"
          :on-contextmenu="onRowContextMenu"
          :ui="{ tr: readOnly ? '' : 'cursor-pointer' }"
        >
          <template #index-cell="{ row }">{{ row.index + 1 }}</template>
          <template #category-cell="{ row }">{{
            row.original.item_category?.name ?? '—'
          }}</template>
          <template #subcategory-cell="{ row }">{{
            row.original.item_subcategory?.name ?? '—'
          }}</template>
          <template #scenarioNames-cell="{ row }"
            ><ScenarioBadges :names="itemScenarioNames(row.original)"
          /></template>
          <template #actions-cell="{ row }">
            <UDropdownMenu :items="menuItems(row.original)" :content="{ align: 'end' }">
              <UButton
                icon="i-lucide-more-vertical"
                color="neutral"
                variant="ghost"
                square
                aria-label="Item options"
              />
            </UDropdownMenu>
          </template>
        </UTable>
      </UContextMenu>
    </div>

    <UModal
      v-model:open="itemDialogVisible"
      :title="editingItemId === null ? 'Add item' : 'Edit item'"
      :ui="{ content: 'max-w-md', footer: 'justify-end' }"
    >
      <template #body>
        <div class="flex flex-col gap-4">
          <ScenarioMultiSelect
            v-model="itemScenarioIds"
            :scenarios="scenarios"
            required
            :error="itemScenarioError"
          />
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
          <UAlert
            v-if="itemSaveError"
            color="error"
            variant="outline"
            :description="itemSaveError"
          />
        </div>
      </template>
      <template #footer>
        <UButton
          label="Cancel"
          icon="i-lucide-x"
          variant="ghost"
          @click="itemDialogVisible = false"
        />
        <UButton
          :label="
            editingItemId === null && itemQuantity > 1 ? `Save ${itemQuantity} items` : 'Save'
          "
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
        <div class="flex flex-col gap-3" data-tour="item-picker">
          <ScenarioMultiSelect
            v-model="pickerScenarioIds"
            :scenarios="scenarios"
            label="Add to scenarios"
            required
            :error="pickerScenarioError"
          />
          <UInput
            v-model="pickerSearch"
            type="text"
            icon="i-lucide-search"
            placeholder="Search the item catalog"
            class="w-full"
          />

          <UTable
            :data="visibleCatalogItems"
            :columns="pickerColumns"
            :get-row-id="(item: Item) => item.id"
            :loading="addingExistingItem"
            sticky
            class="max-h-112"
            :ui="{ tr: 'cursor-pointer' }"
            :on-select="(_e: Event, row: TableRow<Item>) => addExistingItem(row.original)"
          >
            <template #empty>
              <div class="flex flex-col items-center gap-2 py-4">
                <p class="text-sm text-surface-500 dark:text-surface-400">
                  No matching item in the catalog.
                </p>
                <UButton
                  label="Create new item"
                  icon="i-lucide-plus"
                  variant="outline"
                  size="sm"
                  @click="openCreateItemDialogFromPicker()"
                />
              </div>
            </template>
            <template #item-cell="{ row }">{{ describeCatalogItem(row.original) }}</template>
            <template #description-cell="{ row }">{{ row.original.description }}</template>
          </UTable>
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
