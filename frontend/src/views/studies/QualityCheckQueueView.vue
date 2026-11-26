<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { TableColumn } from '@nuxt/ui'
import { getReviewQueue } from '@/api/studyReview'
import type { ReviewQueueEntry, ReviewStatus } from '@/api/types'
import { manualSorting, useTableView } from '@/composables/useTableView'
import { sortHeader } from '@/composables/tableColumns'
import TableFilterDrawer from '@/components/ui/TableFilterDrawer.vue'
import {
  formatDateTime,
  reviewStatusLabels,
  reviewStatusOf,
} from '@/components/studies/review/reviewLabels'
import TablePagination from '@/components/ui/TablePagination.vue'

// Studies their laboratories submitted for quality check, and those sent back
// for changes. The review itself - comments, changes between rounds, the
// decision - happens on the study page.

const entries = ref<ReviewQueueEntry[]>([])
const loading = ref(false)
const loadError = ref('')

const statusOptions = (['in_review', 'changes_requested'] as ReviewStatus[]).map((value) => ({
  label: reviewStatusLabels[value].label,
  value,
}))

const view = useTableView(entries, {
  searchFields: ['title', 'laboratory_name', 'year'],
  filters: {
    title: { field: 'title' },
    laboratory: { field: 'laboratory_name' },
    status: { field: 'status', mode: 'equals' },
  },
  // Waiting for a checker first, oldest submission first.
  sorting: [{ id: 'submitted_at', desc: false }],
  sortAccessors: {
    laboratory: 'laboratory_name',
    progress: (entry) =>
      entry.progress.total ? entry.progress.resolved / entry.progress.total : 1,
  },
})

const columns: TableColumn<ReviewQueueEntry>[] = [
  { id: 'title', accessorKey: 'title', header: sortHeader('Title') },
  { id: 'laboratory', header: sortHeader('Laboratory') },
  {
    id: 'status',
    accessorKey: 'status',
    header: sortHeader('Status'),
    meta: { class: { td: 'w-44' } },
  },
  {
    id: 'round_number',
    accessorKey: 'round_number',
    header: sortHeader('Round'),
    meta: { class: { td: 'w-20' } },
  },
  { id: 'progress', header: sortHeader('Comments resolved'), meta: { class: { td: 'w-48' } } },
  {
    id: 'submitted_at',
    accessorKey: 'submitted_at',
    header: sortHeader('Submitted'),
    meta: { class: { td: 'w-44' } },
  },
  { id: 'actions', header: '', meta: { class: { td: 'w-28 text-right' } } },
]

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    entries.value = await getReviewQueue()
  } catch {
    loadError.value = 'Could not load the studies waiting for quality check.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="flex flex-col gap-6">
    <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Quality Check</h1>

    <UAlert v-if="loadError" color="error" variant="outline" :description="loadError" />

    <div class="flex flex-col gap-3">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <UInput
          v-model="view.search"
          icon="i-lucide-search"
          placeholder="Keyword Search"
          class="w-full max-w-sm"
        />
        <TableFilterDrawer :active-count="view.activeFilterCount" @reset="view.resetFilters()">
          <UFormField label="Status">
            <USelectMenu
              v-model="view.filters.status"
              :items="statusOptions"
              value-key="value"
              placeholder="Any status"
              clear
              class="w-full"
            />
          </UFormField>
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
        </TableFilterDrawer>
      </div>

      <UTable
        v-model:sorting="view.sorting"
        :sorting-options="manualSorting"
        :data="view.rows"
        :columns="columns"
        :loading="loading"
        :get-row-id="(entry: ReviewQueueEntry) => entry.study_id"
        empty="No studies are waiting for a quality check."
      >
        <template #title-cell="{ row }">
          <span class="font-medium">{{ row.original.title || 'Untitled study' }}</span>
          <span v-if="row.original.year" class="text-muted"> ({{ row.original.year }})</span>
        </template>
        <template #laboratory-cell="{ row }">
          {{ row.original.laboratory_name ?? '—' }}
        </template>
        <template #status-cell="{ row }">
          <UBadge
            :label="reviewStatusOf(row.original.status).label"
            :color="reviewStatusOf(row.original.status).color"
            :icon="reviewStatusOf(row.original.status).icon"
            variant="subtle"
            size="sm"
          />
        </template>
        <template #progress-cell="{ row }">
          <div v-if="row.original.progress.total" class="flex flex-col gap-1">
            <span class="text-xs text-muted">
              {{ row.original.progress.resolved }} / {{ row.original.progress.total }}
              <template v-if="row.original.progress.addressed">
                · {{ row.original.progress.addressed }} addressed
              </template>
            </span>
            <UProgress
              :model-value="row.original.progress.resolved"
              :max="row.original.progress.total"
              color="success"
              size="xs"
            />
          </div>
          <span v-else class="text-xs text-muted">No comments</span>
        </template>
        <template #submitted_at-cell="{ row }">
          <span class="text-sm">{{ formatDateTime(row.original.submitted_at) }}</span>
        </template>
        <template #actions-cell="{ row }">
          <UButton
            label="Review"
            icon="i-lucide-search-check"
            size="sm"
            :to="{
              name: 'studies-edit',
              params: { id: row.original.study_id },
              query: { review: '1' },
            }"
          />
        </template>
      </UTable>
      <TablePagination
        v-model:page="view.page"
        v-model:page-size="view.pageSize"
        :total="view.total"
      />
    </div>
  </div>
</template>
