<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { TableColumn } from '@nuxt/ui'
import { listStudies, passQualityCheck } from '@/api/studies'
import type { Study } from '@/api/types'
import { manualSorting, useTableView } from '@/composables/useTableView'
import { sortHeader } from '@/composables/tableColumns'
import TableFilterDrawer from '@/components/ui/TableFilterDrawer.vue'

const studies = ref<Study[]>([])
const loading = ref(false)
const loadError = ref('')
const actionError = ref('')
const actingOnId = ref<string | null>(null)

const pendingStudies = computed(() => studies.value.filter((s) => !s.quality_check_passed))

const view = useTableView(pendingStudies, {
  searchFields: ['title', 'laboratory.laboratory_name', 'year'],
  filters: {
    title: { field: 'title' },
    laboratory: { field: 'laboratory.laboratory_name' },
    year: { field: 'year' },
  },
  sortAccessors: { laboratory: 'laboratory.laboratory_name' },
})

const columns: TableColumn<Study>[] = [
  { id: 'title', accessorKey: 'title', header: sortHeader('Title') },
  { id: 'laboratory', header: sortHeader('Laboratory') },
  { id: 'year', accessorKey: 'year', header: sortHeader('Year') },
  { id: 'actions', header: '', meta: { class: { td: 'w-48 text-right' } } },
]

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    studies.value = await listStudies()
  } catch {
    loadError.value = 'Could not load studies.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function approve(study: Study) {
  if (
    !window.confirm('Pass the quality check for this study? This will also publish it immediately.')
  ) {
    return
  }
  actionError.value = ''
  actingOnId.value = study.id
  try {
    const updated = await passQualityCheck(study.id)
    studies.value = studies.value.map((s) => (s.id === updated.id ? updated : s))
  } catch {
    actionError.value = 'Could not pass the quality check for this study. Please try again.'
  } finally {
    actingOnId.value = null
  }
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Quality Check</h1>

    <UAlert v-if="loadError" color="error" variant="outline" :description="loadError" />
    <UAlert v-if="actionError" color="error" variant="outline" :description="actionError" />

    <div class="flex flex-col gap-3">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <UInput
          v-model="view.search"
          icon="i-lucide-search"
          placeholder="Keyword Search"
          class="w-full max-w-sm"
        />
        <TableFilterDrawer :active-count="view.activeFilterCount" @reset="view.resetFilters()">
          <UFormField label="Title">
            <UInput v-model="view.filters.title" placeholder="Search by title" class="w-full" />
          </UFormField>
          <UFormField label="Laboratory">
            <UInput
              v-model="view.filters.laboratory"
              placeholder="Search by laboratory"
              class="w-full"
            />
          </UFormField>
          <UFormField label="Year">
            <UInput v-model="view.filters.year" placeholder="Search by year" class="w-full" />
          </UFormField>
        </TableFilterDrawer>
      </div>

      <UTable
        v-model:sorting="view.sorting"
        :sorting-options="manualSorting"
        :data="view.rows"
        :columns="columns"
        :loading="loading"
        :get-row-id="(study: Study) => study.id"
        empty="No studies are waiting for a quality check."
      >
        <template #laboratory-cell="{ row }">
          {{ row.original.laboratory?.laboratory_name ?? '—' }}
        </template>
        <template #actions-cell="{ row }">
          <UButton
            label="Pass quality check"
            size="sm"
            :loading="actingOnId === row.original.id"
            @click="approve(row.original)"
          />
        </template>
      </UTable>
    </div>
  </div>
</template>
