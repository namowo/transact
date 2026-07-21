<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Message from 'primevue/message'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'
import { FilterMatchMode } from '@primevue/core/api'
import { getLabMethodConfig } from '@/data/labMethods'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{ methodKey: string }>()

const router = useRouter()
const config = computed(() => getLabMethodConfig(props.methodKey))
const auth = useAuthStore()
const laboratoryId = computed(() => auth.user?.laboratory_id ?? null)

type MethodRow = Record<string, unknown> & { id: number; laboratory_id?: number | null }

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
  return (value as string | number | null | undefined) ?? '—'
}
</script>

<template>
  <div v-if="config" class="flex flex-col gap-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">
        {{ config.label }} methods
      </h1>
      <Button label="Add entry" icon="pi pi-plus" @click="openCreate" />
    </div>

    <Message v-if="loadError" severity="error" size="small">{{ loadError }}</Message>

    <div class="overflow-x-auto">
      <div class="mb-3 flex items-center justify-between gap-3">
        <Button type="button" variant="outlined" size="small" @click="clearFilters()">
          <i class="pi pi-filter-slash" />
          Clear Filters
        </Button>
        <IconField iconPosition="left">
          <InputIcon class="pi pi-search" />
          <InputText v-model="filters['global'].value" type="text" placeholder="Keyword Search" />
        </IconField>
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
          :header="config.fields.find((f) => f.key === colKey)?.label ?? colKey"
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #body="{ data }">{{ columnValue(data, colKey) }}</template>
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" type="text" placeholder="Search" />
          </template>
        </Column>
        <Column header="" style="width: 6rem">
          <template #body="{ data }">
            <div class="flex gap-1 justify-end">
              <Button icon="pi pi-pencil" text rounded aria-label="Edit" @click="openEdit(data)" />
              <Button
                icon="pi pi-trash"
                text
                rounded
                severity="danger"
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
