<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getLabMethodConfig, pcrMethodLabel } from '@/data/labMethods'
import { useAuthStore } from '@/stores/auth'
import LabMethodFormModal from './LabMethodFormModal.vue'
import type { TableColumn } from '@nuxt/ui'
import { manualSorting, useTableView } from '@/composables/useTableView'
import { sortHeader } from '@/composables/tableColumns'
import TableFilterDrawer from '@/components/ui/TableFilterDrawer.vue'
import TablePagination from '@/components/ui/TablePagination.vue'

const props = defineProps<{ methodKey: string }>()

const route = useRoute()
const router = useRouter()

const config = computed(() => getLabMethodConfig(props.methodKey))
const auth = useAuthStore()
const laboratoryId = computed(() => auth.user?.laboratory_id ?? null)

type MethodRow = Record<string, unknown> & { id: string; laboratory_id?: string | null }

const items = ref<MethodRow[]>([])
const loading = ref(false)
const loadError = ref('')

// Per-column text filters; which columns there are depends on the method.
const columnFilters = reactive<Record<string, string>>({})
const activeFilterCount = computed(
  () => Object.values(columnFilters).filter((v) => v?.trim()).length,
)

function clearFilters() {
  for (const key of Object.keys(columnFilters)) delete columnFilters[key]
}

const columnFilteredItems = computed(() => {
  const active = Object.entries(columnFilters).filter(([, value]) => value?.trim())
  if (!active.length) return items.value
  return items.value.filter((row) =>
    active.every(([key, value]) =>
      String(columnValue(row, key)).toLocaleLowerCase().includes(value.trim().toLocaleLowerCase()),
    ),
  )
})

const view = useTableView(columnFilteredItems, {
  searchFields: [(row) => (config.value?.listColumns ?? []).map((key) => columnValue(row, key))],
  sortValue: (row, key) => {
    const value = columnValue(row, key)
    return value === '—' ? null : value
  },
  pageSize: 10,
})

function columnLabel(key: string) {
  return (
    config.value?.fields.find((f) => f.key === key || f.key === `${key}_id`)?.label ??
    config.value?.listColumnLabels?.[key] ??
    key
  )
}

const columns = computed<TableColumn<MethodRow>[]>(() => [
  ...(config.value?.listColumns ?? []).map((key) => ({
    id: key,
    header: sortHeader(columnLabel(key)),
  })),
  { id: 'actions', header: '', meta: { class: { td: 'w-36' } } },
])

// The open modal (and which row it's editing) is kept in the `entry` query
// param, so it survives a full page reload (e.g. a dev HMR fallback)
// instead of silently discarding an in-progress edit.
const entryQuery = computed(() => route.query.entry as string | undefined)

async function load() {
  if (!config.value) return
  loading.value = true
  loadError.value = ''
  clearFilters()
  view.reset()
  view.sorting = []
  try {
    const all = (await config.value.api.list()) as MethodRow[]
    const scoped = config.value.laboratoryScoped
      ? all.filter((item) => item.laboratory_id === laboratoryId.value)
      : all
    // Display-only; the form builds its payload from `fields`, so this
    // extra key never reaches the API.
    const labels = config.value.rowLabels?.(scoped)
    items.value = labels ? scoped.map((item) => ({ ...item, label: labels[item.id] })) : scoped
    syncModalFromQuery()
  } catch {
    loadError.value = 'Could not load this list. Please try again.'
  } finally {
    loading.value = false
  }
}

function syncModalFromQuery() {
  duplicateFrom.value = null
  if (!entryQuery.value) {
    modalVisible.value = false
    editingRow.value = null
    return
  }
  if (entryQuery.value === 'new') {
    editingRow.value = null
  } else {
    editingRow.value = items.value.find((item) => item.id === entryQuery.value) ?? null
  }
  modalVisible.value = true
}

onMounted(load)
watch(() => props.methodKey, load)
watch(entryQuery, syncModalFromQuery)

const modalVisible = ref(false)
const editingRow = ref<MethodRow | null>(null)
// Not persisted in the `entry` query param (unlike editingRow) - a
// duplicated-from source only matters for the one dialog session that
// pre-fills the new entry, not across a reload.
const duplicateFrom = ref<MethodRow | null>(null)

watch(modalVisible, (isOpen) => {
  const entry = isOpen ? (editingRow.value?.id ?? 'new') : undefined
  if (entry === entryQuery.value) return
  router.replace({ query: { ...route.query, entry } })
})

function openCreate() {
  if (!config.value) return
  editingRow.value = null
  duplicateFrom.value = null
  modalVisible.value = true
}

function openEdit(row: MethodRow) {
  if (!config.value) return
  editingRow.value = row
  duplicateFrom.value = null
  modalVisible.value = true
}

function openDuplicate(row: MethodRow) {
  if (!config.value) return
  editingRow.value = null
  duplicateFrom.value = row
  modalVisible.value = true
}

async function deleteRow(row: MethodRow) {
  if (!config.value) return
  if (!window.confirm('Delete this entry? This cannot be undone.')) return
  try {
    await config.value.api.delete(row.id)
    items.value = items.value.filter((item) => item.id !== row.id)
  } catch {
    loadError.value = 'Could not delete this entry. Please try again.'
  }
}

function columnValue(row: MethodRow, key: string) {
  const value = row[key]
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (key === 'pcr_method') {
    return value ? pcrMethodLabel(value as Parameters<typeof pcrMethodLabel>[0]) : '—'
  }
  if (value && typeof value === 'object' && 'name' in value) {
    return (value as { name?: string | null }).name ?? '—'
  }
  return (value as string | number | null | undefined) ?? '—'
}
</script>

<template>
  <div v-if="config" class="flex flex-col gap-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">
        {{ config.label }} methods
      </h1>
      <UButton
        :label="`Add ${config.entryLabel ?? 'entry'}`"
        icon="i-lucide-plus"
        @click="openCreate"
      />
    </div>

    <UAlert v-if="loadError" color="error" variant="outline" :description="loadError" />

    <div class="flex flex-col gap-3">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <UInput
          v-model="view.search"
          icon="i-lucide-search"
          placeholder="Keyword Search"
          class="w-full max-w-sm"
        />
        <TableFilterDrawer :active-count="activeFilterCount" @reset="clearFilters()">
          <UFormField
            v-for="colKey in config.listColumns"
            :key="colKey"
            :label="columnLabel(colKey)"
          >
            <UInput v-model="columnFilters[colKey]" placeholder="Search" class="w-full" />
          </UFormField>
        </TableFilterDrawer>
      </div>

      <UTable
        v-model:sorting="view.sorting"
        :sorting-options="manualSorting"
        :data="view.rows"
        :columns="columns"
        :loading="loading"
        :get-row-id="(row: MethodRow) => row.id"
        empty="No entries found."
      >
        <template v-for="colKey in config.listColumns" :key="colKey" #[`${colKey}-cell`]="{ row }">
          {{ columnValue(row.original, colKey) }}
        </template>
        <template #actions-cell="{ row }">
          <div class="flex gap-1 justify-end">
            <UButton
              icon="i-lucide-pencil"
              variant="ghost"
              square
              aria-label="Edit"
              @click="openEdit(row.original)"
            />
            <UButton
              icon="i-lucide-copy"
              variant="ghost"
              square
              aria-label="Duplicate"
              @click="openDuplicate(row.original)"
            />
            <UButton
              icon="i-lucide-trash-2"
              variant="ghost"
              square
              color="error"
              aria-label="Delete"
              @click="deleteRow(row.original)"
            />
          </div>
        </template>
      </UTable>
      <TablePagination
        v-model:page="view.page"
        v-model:page-size="view.pageSize"
        :total="view.total"
      />
    </div>

    <LabMethodFormModal
      v-model:visible="modalVisible"
      :method-key="methodKey"
      :editing-row="editingRow"
      :duplicate-from="duplicateFrom"
      @saved="load"
    />
  </div>
</template>
