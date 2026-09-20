<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import { FilterMatchMode } from '@primevue/core/api'
import { getLabMethodConfig } from '@/data/labMethods'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{ methodKey: string }>()

const router = useRouter()
const config = computed(() => getLabMethodConfig(props.methodKey))
const auth = useAuthStore()
const laboratoryId = computed(() => auth.user?.laboratory_id ?? null)

type MethodRow = Record<string, unknown> & { id: string; laboratory_id?: string | null }

const items = ref<MethodRow[]>([])
const loading = ref(false)
const loadError = ref('')

function initFilters() {
  const columnFilters = Object.fromEntries(
    (config.value?.listColumns ?? []).map((key) => [
      key,
      { value: null, matchMode: FilterMatchMode.CONTAINS },
    ]),
  )
  return {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
    ...columnFilters,
  }
}

const filters = ref(initFilters())

function clearFilters() {
  filters.value = initFilters()
}

async function load() {
  if (!config.value) return
  loading.value = true
  loadError.value = ''
  filters.value = initFilters()
  try {
    const all = (await config.value.api.list()) as MethodRow[]
    items.value = config.value.laboratoryScoped
      ? all.filter((item) => item.laboratory_id === laboratoryId.value)
      : all
  } catch {
    loadError.value = 'Could not load this list. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => props.methodKey, load)

function openCreate() {
  if (!config.value) return
  router.push({ name: `settings-methods-${config.value.key}-new` })
}

function openEdit(row: MethodRow) {
  if (!config.value) return
  router.push({ name: `settings-methods-${config.value.key}-edit`, params: { id: String(row.id) } })
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
      <UButton label="Add entry" icon="i-lucide-plus" @click="openCreate" />
    </div>

    <UAlert v-if="loadError" color="error" variant="outline" :description="loadError" />

    <div class="overflow-x-auto">
      <div class="mb-3 flex items-center justify-between gap-3">
        <UButton type="button" icon="i-lucide-filter-x" variant="outline" size="sm" @click="clearFilters()">
          Clear Filters
        </UButton>
        <UInput
          v-model="filters['global'].value"
          type="text"
          icon="i-lucide-search"
          placeholder="Keyword Search"
        />
      </div>

      <DataTable
        v-model:filters="filters"
        :value="items"
        :loading="loading"
        data-key="id"
        filterDisplay="menu"
        removableSort
        paginator
        :rows="10"
        :rowsPerPageOptions="[10, 25, 50]"
        :globalFilterFields="config.listColumns"
      >
        <template #empty>No entries found.</template>

        <Column
          v-for="colKey in config.listColumns"
          :key="colKey"
          :field="colKey"
          :header="
            config.fields.find((f) => f.key === colKey || f.key === `${colKey}_id`)?.label ??
            colKey
          "
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #body="{ data }">{{ columnValue(data, colKey) }}</template>
          <template #filter="{ filterModel }">
            <UInput v-model="filterModel.value" type="text" placeholder="Search" />
          </template>
        </Column>
        <Column header="" style="width: 6rem">
          <template #body="{ data }">
            <div class="flex gap-1 justify-end">
              <UButton icon="i-lucide-pencil" variant="ghost" square aria-label="Edit" @click="openEdit(data)" />
              <UButton
                icon="i-lucide-trash-2"
                variant="ghost"
                square
                color="error"
                aria-label="Delete"
                @click="deleteRow(data)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>
