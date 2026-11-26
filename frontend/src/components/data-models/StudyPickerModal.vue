<script setup lang="ts">
import { computed, h, ref, resolveComponent, watch } from 'vue'
import type { TableColumn, TableRow } from '@nuxt/ui'
import type { DownloadableStudy } from '@/api/types'
import TableLoadingSkeleton from '@/components/ui/TableLoadingSkeleton.vue'
import { manualSorting, useTableView } from '@/composables/useTableView'
import TablePagination from '@/components/ui/TablePagination.vue'

const props = defineProps<{
  studies: DownloadableStudy[]
  loading?: boolean
  selected: string[]
}>()

const emit = defineEmits<{ apply: [ids: string[]] }>()

const open = defineModel<boolean>('open', { default: false })

const UButton = resolveComponent('UButton')

// The selection is a draft until applied, so Cancel leaves it untouched.
const draft = ref(new Set<string>())
const search = ref('')
const laboratories = ref<string[]>([])
const status = ref<'all' | 'published' | 'unpublished'>('all')
const selectedOnly = ref(false)
const sorting = ref<{ id: string; desc: boolean }[]>([{ id: 'year', desc: true }])

watch(open, (isOpen) => {
  if (!isOpen) return
  draft.value = new Set(props.selected)
  search.value = ''
  laboratories.value = []
  status.value = 'all'
  selectedOnly.value = false
})

const laboratoryItems = computed(() =>
  [...new Set(props.studies.map((s) => s.laboratory_name).filter((n): n is string => !!n))].sort(
    (a, b) => a.localeCompare(b),
  ),
)

const hasUnpublished = computed(() => props.studies.some((s) => !s.published))

const filtersActive = computed(
  () =>
    !!search.value.trim() ||
    laboratories.value.length > 0 ||
    status.value !== 'all' ||
    selectedOnly.value,
)

function resetFilters() {
  search.value = ''
  laboratories.value = []
  status.value = 'all'
  selectedOnly.value = false
}

const filtered = computed(() => {
  const terms = search.value.toLowerCase().split(/\s+/).filter(Boolean)
  const labs = new Set(laboratories.value)
  return props.studies.filter((study) => {
    if (selectedOnly.value && !draft.value.has(study.id)) return false
    if (labs.size && !labs.has(study.laboratory_name ?? '')) return false
    if (status.value === 'published' && !study.published) return false
    if (status.value === 'unpublished' && study.published) return false
    if (!terms.length) return true
    const haystack = [
      study.title,
      study.year,
      study.laboratory_name,
      study.journal,
      study.doi,
      ...study.authors,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
    return terms.every((term) => haystack.includes(term))
  })
})

// Sorted, then one page at a time; a new search or filter starts on page 1.
const view = useTableView(filtered, {
  sorting,
  sortAccessors: {
    year: (s) => (s.year ? Number.parseInt(s.year, 10) || undefined : undefined),
    laboratory: 'laboratory_name',
  },
})
watch([search, laboratories, status, selectedOnly], () => (view.page = 1))

const visibleDraftCount = computed(() => props.studies.filter((s) => draft.value.has(s.id)).length)

const visibleSelected = computed(() => filtered.value.filter((s) => draft.value.has(s.id)).length)

const headerChecked = computed<boolean | 'indeterminate'>(() => {
  if (!filtered.value.length || !visibleSelected.value) return false
  return visibleSelected.value === filtered.value.length ? true : 'indeterminate'
})

function toggle(id: string) {
  const next = new Set(draft.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  draft.value = next
}

// Acts on the rows currently shown, so "filter, then select all" works.
function toggleVisible() {
  const next = new Set(draft.value)
  const select = headerChecked.value !== true
  for (const study of filtered.value) {
    if (select) next.add(study.id)
    else next.delete(study.id)
  }
  draft.value = next
}

function onRowSelect(_event: Event, row: TableRow<DownloadableStudy>) {
  toggle(row.original.id)
}

function sortHeader(label: string) {
  return ({
    column,
  }: {
    column: { getIsSorted: () => false | 'asc' | 'desc'; toggleSorting: (desc?: boolean) => void }
  }) => {
    const sorted = column.getIsSorted()
    return h(UButton, {
      color: 'neutral',
      variant: 'ghost',
      label,
      icon: sorted
        ? sorted === 'asc'
          ? 'i-lucide-arrow-up-narrow-wide'
          : 'i-lucide-arrow-down-wide-narrow'
        : 'i-lucide-arrow-up-down',
      class: '-mx-2.5',
      onClick: () => column.toggleSorting(sorted === 'asc'),
    })
  }
}

const columns: TableColumn<DownloadableStudy>[] = [
  { id: 'select', header: '', enableSorting: false, meta: { class: { td: 'w-10' } } },
  { accessorKey: 'title', header: sortHeader('Study') },
  {
    id: 'year',
    accessorFn: (s) => (s.year ? Number.parseInt(s.year, 10) || undefined : undefined),
    header: sortHeader('Year'),
    sortUndefined: 'last',
  },
  {
    id: 'laboratory',
    accessorFn: (s) => s.laboratory_name ?? undefined,
    header: sortHeader('Laboratory'),
    sortUndefined: 'last',
  },
  {
    accessorKey: 'scenario_count',
    header: sortHeader('Scenarios'),
    meta: { class: { td: 'text-right tabular-nums', th: 'text-right' } },
  },
  {
    accessorKey: 'sample_count',
    header: sortHeader('Samples'),
    meta: { class: { td: 'text-right tabular-nums', th: 'text-right' } },
  },
]

function authorLine(study: DownloadableStudy) {
  const { authors } = study
  if (!authors.length) return ''
  return authors.length > 3 ? `${authors.slice(0, 3).join(', ')} et al.` : authors.join(', ')
}

function apply() {
  // Keep the order of the list the studies came in, not click order. Ids
  // the viewer can't see (e.g. in a shared model) are kept as they were.
  const known = new Set(props.studies.map((s) => s.id))
  const hidden = props.selected.filter((id) => !known.has(id))
  emit('apply', [...props.studies.filter((s) => draft.value.has(s.id)).map((s) => s.id), ...hidden])
  open.value = false
}
</script>

<template>
  <UModal
    v-model:open="open"
    title="Choose studies"
    description="Search, filter and sort the studies, then tick the ones you want to download."
    :ui="{ content: 'sm:max-w-5xl', body: 'flex flex-col gap-3' }"
  >
    <template #body>
      <div class="flex flex-wrap items-center gap-2">
        <UInput
          v-model="search"
          icon="i-lucide-search"
          placeholder="Search title, author, journal, DOI…"
          class="min-w-56 flex-1"
          autofocus
        />
        <USelectMenu
          v-if="laboratoryItems.length > 1"
          v-model="laboratories"
          :items="laboratoryItems"
          multiple
          placeholder="All laboratories"
          icon="i-lucide-building-2"
          class="w-56"
        />
        <USelect
          v-if="hasUnpublished"
          v-model="status"
          :items="[
            { label: 'All statuses', value: 'all' },
            { label: 'Published', value: 'published' },
            { label: 'Unpublished (my laboratory)', value: 'unpublished' },
          ]"
          class="w-56"
        />
        <USwitch v-model="selectedOnly" label="Selected only" />
        <UButton
          v-if="filtersActive"
          label="Reset filters"
          variant="link"
          color="neutral"
          icon="i-lucide-x"
          @click="resetFilters"
        />
      </div>

      <UTable
        v-model:sorting="view.sorting"
        :sorting-options="manualSorting"
        :data="view.rows"
        :columns="columns"
        :loading="loading"
        :get-row-id="(s: DownloadableStudy) => s.id"
        :empty="filtersActive ? 'No studies match these filters.' : 'No studies available.'"
        sticky
        class="max-h-[55vh] rounded-md border border-default"
        :ui="{ tr: 'cursor-pointer', td: 'py-2 align-top text-sm' }"
        @select="onRowSelect"
      >
        <template #loading>
          <TableLoadingSkeleton />
        </template>
        <template #select-header>
          <UCheckbox
            :model-value="headerChecked"
            :disabled="!filtered.length"
            aria-label="Select all shown studies"
            @update:model-value="toggleVisible"
          />
        </template>
        <template #select-cell="{ row }">
          <UCheckbox
            :model-value="draft.has(row.original.id)"
            :aria-label="`Select ${row.original.title}`"
            @click.stop
            @update:model-value="toggle(row.original.id)"
          />
        </template>
        <template #title-cell="{ row }">
          <div class="flex min-w-64 max-w-xl flex-col gap-0.5 whitespace-normal">
            <span class="font-medium text-highlighted">{{ row.original.title }}</span>
            <span v-if="row.original.authors.length" class="text-xs text-muted">
              {{ authorLine(row.original) }}
            </span>
            <span v-if="row.original.journal || row.original.doi" class="text-xs text-muted">
              <template v-if="row.original.journal">{{ row.original.journal }}</template>
              <template v-if="row.original.journal && row.original.doi"> · </template>
              <template v-if="row.original.doi">DOI {{ row.original.doi }}</template>
            </span>
            <UBadge
              v-if="!row.original.published"
              label="Unpublished, my laboratory"
              color="warning"
              variant="subtle"
              size="sm"
              class="mt-1 self-start"
            />
          </div>
        </template>
        <template #year-cell="{ row }">{{ row.original.year ?? '–' }}</template>
        <template #laboratory-cell="{ row }">
          <span class="whitespace-normal">{{ row.original.laboratory_name ?? '–' }}</span>
        </template>
      </UTable>
      <TablePagination
        v-model:page="view.page"
        v-model:page-size="view.pageSize"
        :total="view.total"
      />

      <p class="text-xs text-muted">
        Click a row or its checkbox to select it. The checkbox in the header selects or clears all
        studies currently shown.
      </p>
    </template>

    <template #footer>
      <div class="flex w-full flex-wrap items-center gap-2">
        <span class="text-sm text-muted">
          {{ visibleDraftCount }} of {{ studies.length }}
          {{ studies.length === 1 ? 'study' : 'studies' }} selected
          <template v-if="filtersActive"> · {{ filtered.length }} shown</template>
        </span>
        <UButton
          v-if="visibleDraftCount"
          label="Clear selection"
          variant="link"
          color="neutral"
          @click="draft = new Set()"
        />
        <div class="ms-auto flex gap-2">
          <UButton label="Cancel" color="neutral" variant="outline" @click="open = false" />
          <UButton
            :label="
              visibleDraftCount
                ? `Use ${visibleDraftCount} ${visibleDraftCount === 1 ? 'study' : 'studies'}`
                : 'Apply'
            "
            icon="i-lucide-check"
            @click="apply"
          />
        </div>
      </div>
    </template>
  </UModal>
</template>
