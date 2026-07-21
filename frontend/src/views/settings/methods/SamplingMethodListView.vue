<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Message from 'primevue/message'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'
import { FilterMatchMode } from '@primevue/core/api'
import { useAuthStore } from '@/stores/auth'
import { samplingMethodApi } from '@/api/methods'
import type { SamplingMethod } from '@/api/types'

const router = useRouter()
const auth = useAuthStore()
const laboratoryId = computed(() => auth.user?.laboratory_id ?? null)

const items = ref<SamplingMethod[]>([])
const loading = ref(false)
const loadError = ref('')

function describeSubMethod(m: { id: number; description?: string | null } | null | undefined) {
  if (!m) return '—'
  return m.description?.trim() || `#${m.id}`
}

function initFilters() {
  return {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
    swab_description: { value: null, matchMode: FilterMatchMode.CONTAINS },
    tape_description: { value: null, matchMode: FilterMatchMode.CONTAINS },
    vacuum_description: { value: null, matchMode: FilterMatchMode.CONTAINS },
    cutting_description: { value: null, matchMode: FilterMatchMode.CONTAINS },
    scraping_description: { value: null, matchMode: FilterMatchMode.CONTAINS },
    picking_description: { value: null, matchMode: FilterMatchMode.CONTAINS },
  }
}

const filters = ref(initFilters())

function clearFilters() {
  filters.value = initFilters()
}

type SamplingMethodRow = SamplingMethod & {
  swab_description: string
  tape_description: string
  vacuum_description: string
  cutting_description: string
  scraping_description: string
  picking_description: string
}

const rows = computed<SamplingMethodRow[]>(() =>
  items.value.map((item) => ({
    ...item,
    swab_description: describeSubMethod(item.swab_method),
    tape_description: describeSubMethod(item.tape_method),
    vacuum_description: describeSubMethod(item.vacuum_method),
    cutting_description: describeSubMethod(item.cutting_method),
    scraping_description: describeSubMethod(item.scraping_method),
    picking_description: describeSubMethod(item.picking_method),
  })),
)

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const all = await samplingMethodApi.list()
    items.value = all.filter((item) => item.laboratory_id === laboratoryId.value)
  } catch {
    loadError.value = 'Could not load sampling methods. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

function openCreate() {
  router.push({ name: 'settings-methods-sampling-new' })
}

function openEdit(row: SamplingMethod) {
  router.push({ name: 'settings-methods-sampling-edit', params: { id: String(row.id) } })
}

async function deleteRow(row: SamplingMethod) {
  if (!window.confirm('Delete this entry? This cannot be undone.')) return
  try {
    await samplingMethodApi.delete(row.id)
    items.value = items.value.filter((item) => item.id !== row.id)
  } catch {
    loadError.value = 'Could not delete this entry. Please try again.'
  }
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Sampling methods</h1>
      <Button label="Add sampling method" icon="pi pi-plus" @click="openCreate" />
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
        :value="rows"
        :loading="loading"
        data-key="id"
        filterDisplay="menu"
        removableSort
        paginator
        :rows="10"
        :rowsPerPageOptions="[10, 25, 50]"
        :globalFilterFields="[
          'swab_description',
          'tape_description',
          'vacuum_description',
          'cutting_description',
          'scraping_description',
          'picking_description',
        ]"
      >
        <template #empty>No entries found.</template>

        <Column
          field="swab_description"
          header="Swab"
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" type="text" placeholder="Search" />
          </template>
        </Column>
        <Column
          field="tape_description"
          header="Tape"
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" type="text" placeholder="Search" />
          </template>
        </Column>
        <Column
          field="vacuum_description"
          header="Vacuum"
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" type="text" placeholder="Search" />
          </template>
        </Column>
        <Column
          field="cutting_description"
          header="Cutting"
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" type="text" placeholder="Search" />
          </template>
        </Column>
        <Column
          field="scraping_description"
          header="Scraping"
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #filter="{ filterModel }">
            <InputText v-model="filterModel.value" type="text" placeholder="Search" />
          </template>
        </Column>
        <Column
          field="picking_description"
          header="Picking"
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
        >
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
