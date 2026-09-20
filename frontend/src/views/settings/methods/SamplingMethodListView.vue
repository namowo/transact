<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import { FilterMatchMode } from '@openvue/core/api'
import { useAuthStore } from '@/stores/auth'
import { samplingMethodApi } from '@/api/methods'
import type { SamplingMethod } from '@/api/types'

const router = useRouter()
const auth = useAuthStore()
const laboratoryId = computed(() => auth.user?.laboratory_id ?? null)

const items = ref<SamplingMethod[]>([])
const loading = ref(false)
const loadError = ref('')

function describeSubMethod(m: { id: string; description?: string | null } | null | undefined) {
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
      <UButton label="Add sampling method" icon="i-lucide-plus" @click="openCreate" />
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
            <UInput v-model="filterModel.value" type="text" placeholder="Search" />
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
            <UInput v-model="filterModel.value" type="text" placeholder="Search" />
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
            <UInput v-model="filterModel.value" type="text" placeholder="Search" />
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
            <UInput v-model="filterModel.value" type="text" placeholder="Search" />
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
            <UInput v-model="filterModel.value" type="text" placeholder="Search" />
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
