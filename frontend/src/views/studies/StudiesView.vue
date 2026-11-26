<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { ContextMenuItem, TableColumn, TableRow } from '@nuxt/ui'
import { listStudies } from '@/api/studies'
import { useAuthStore } from '@/stores/auth'
import { canEditStudy } from '@/composables/useStudyAccess'
import type { ReviewStatus, Study } from '@/api/types'
import { reviewStatusLabels, reviewStatusOf } from '@/components/studies/review/reviewLabels'
import { manualSorting, useTableView } from '@/composables/useTableView'
import { sortHeader } from '@/composables/tableColumns'
import TableFilterDrawer from '@/components/ui/TableFilterDrawer.vue'
import TablePagination from '@/components/ui/TablePagination.vue'
import TableLoadingSkeleton from '@/components/ui/TableLoadingSkeleton.vue'

const props = defineProps<{ scope: 'laboratory' | 'all' }>()

const router = useRouter()
const auth = useAuthStore()

const studies = ref<Study[]>([])
const loading = ref(false)

function formatAuthors(authors: Study['authors']): string {
  return authors
    .map((author) => [author.title, author.first_name, author.last_name].filter(Boolean).join(' '))
    .join(', ')
}

async function load() {
  loading.value = true
  try {
    studies.value = await listStudies()
  } finally {
    loading.value = false
  }
}

onMounted(load)

const scopedStudies = computed(() =>
  props.scope === 'laboratory'
    ? studies.value.filter((study) => study.laboratory_id === auth.user?.laboratory_id)
    : studies.value,
)

const qcStatusOptions = (Object.keys(reviewStatusLabels) as ReviewStatus[]).map((value) => ({
  label: reviewStatusLabels[value].label,
  value,
}))

const view = useTableView(scopedStudies, {
  searchFields: ['title', 'journal', 'doi', 'year', (study) => formatAuthors(study.authors)],
  filters: {
    title: { field: 'title' },
    year: { field: 'year' },
    laboratory: { field: 'laboratory.laboratory_name' },
    qc: { field: (study) => study.review_status ?? 'draft', mode: 'equals' },
  },
  sorting: [{ id: 'created_at', desc: true }],
  sortAccessors: { laboratory: 'laboratory.laboratory_name' },
})

const columns = computed<TableColumn<Study>[]>(() => [
  { id: 'title', accessorKey: 'title', header: sortHeader('Title') },
  { id: 'authors', accessorKey: 'authors', header: 'Authors' },
  { id: 'doi', accessorKey: 'doi', header: 'DOI', meta: { class: { td: 'w-40' } } },
  { id: 'year', accessorKey: 'year', header: sortHeader('Year'), meta: { class: { td: 'w-24' } } },
  { id: 'laboratory', header: sortHeader('Laboratory'), meta: { class: { td: 'w-48' } } },
  { id: 'qc', header: 'QC', meta: { class: { td: 'w-32' } } },
  {
    id: 'created_at',
    accessorKey: 'created_at',
    header: sortHeader('Created'),
    meta: { class: { td: 'w-32' } },
  },
  ...(auth.isAuthenticated ? [{ id: 'actions', header: '', meta: { class: { td: 'w-12' } } }] : []),
])

function isOwnLab(study: Study) {
  return study.laboratory_id === auth.user?.laboratory_id
}

function canEdit(study: Study) {
  return canEditStudy(study, auth.user)
}

// Any signed-in user can open a study; other labs' studies open read-only.
function canOpen() {
  return auth.isAuthenticated
}

function openStep(study: Study, step: 'details' | 'planning' | 'data-entry') {
  router.push({ name: 'studies-edit', params: { id: study.id }, query: { step } })
}

const showPurposeDialog = ref(false)

function choosePurpose(purpose: 'transfer' | 'repository') {
  showPurposeDialog.value = false
  router.push({ name: 'studies-new', query: { purpose } })
}

function menuItems(study: Study): ContextMenuItem[] {
  const editable = canEdit(study)
  return [
    {
      label: 'Details',
      icon: editable ? 'i-lucide-pencil' : 'i-lucide-eye',
      onSelect: () => openStep(study, 'details'),
    },
    {
      label: 'Planning',
      icon: 'i-lucide-network',
      onSelect: () => openStep(study, 'planning'),
    },
    ...(study.add_data_to_repository
      ? [
          {
            label: editable ? 'Add data' : 'Data',
            icon: 'i-lucide-database',
            onSelect: () => openStep(study, 'data-entry'),
          },
        ]
      : []),
    { type: 'separator' },
    {
      // TODO: enable once study data export is implemented
      label: 'Download (coming soon)',
      icon: 'i-lucide-download',
      disabled: true,
    },
  ]
}

// The right-clicked row's menu.
const contextMenuItems = ref<ContextMenuItem[]>([])

function onRowContextMenu(_event: Event, row: TableRow<Study>) {
  contextMenuItems.value = auth.isAuthenticated ? menuItems(row.original) : []
}

function onRowSelect(_event: Event, row: TableRow<Study>) {
  if (!canOpen()) return
  openStep(row.original, 'details')
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">
          {{ props.scope === 'laboratory' ? 'Studies by Laboratory' : 'All Studies' }}
        </h1>
        <p class="text-surface-500 dark:text-surface-400 text-sm mt-1">
          {{
            props.scope === 'laboratory'
              ? 'Studies belonging to your laboratory.'
              : auth.isAuthenticated
                ? 'Studies from all laboratories. Studies from other laboratories open read-only.'
                : 'Published studies from all laboratories.'
          }}
        </p>
      </div>
      <UButton
        v-if="auth.isAuthenticated"
        data-tour="add-study"
        label="Add study"
        icon="i-lucide-plus"
        @click="showPurposeDialog = true"
      />
    </div>

    <div class="flex flex-col gap-3">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <UInput
          v-model="view.search"
          icon="i-lucide-search"
          placeholder="Search title, author, journal, DOI…"
          class="w-full sm:max-w-sm"
        />
        <TableFilterDrawer :active-count="view.activeFilterCount" @reset="view.resetFilters()">
          <UFormField label="Title">
            <UInput v-model="view.filters.title" placeholder="Search by title" class="w-full" />
          </UFormField>
          <UFormField label="Year">
            <UInput v-model="view.filters.year" placeholder="Search by year" class="w-full" />
          </UFormField>
          <UFormField label="Laboratory">
            <UInput
              v-model="view.filters.laboratory"
              placeholder="Search by laboratory"
              class="w-full"
            />
          </UFormField>
          <UFormField label="Quality check">
            <USelectMenu
              v-model="view.filters.qc"
              :items="qcStatusOptions"
              value-key="value"
              placeholder="Any status"
              clear
              class="w-full"
            />
          </UFormField>
        </TableFilterDrawer>
      </div>

      <UContextMenu :items="contextMenuItems" :disabled="!auth.isAuthenticated">
        <UTable
          v-model:sorting="view.sorting"
          :sorting-options="manualSorting"
          :data="view.rows"
          :columns="columns"
          :loading="loading"
          :get-row-id="(study: Study) => study.id"
          empty="No studies found."
          :on-select="canOpen() ? onRowSelect : undefined"
          :on-contextmenu="onRowContextMenu"
          :ui="{ tr: canOpen() ? 'cursor-pointer' : '' }"
        >
          <template #loading>
            <TableLoadingSkeleton />
          </template>
          <template #title-cell="{ row }">
            <span v-if="row.original.title" class="font-medium whitespace-normal">{{
              row.original.title
            }}</span>
            <UBadge v-else label="Not set" color="neutral" variant="subtle" size="sm" />
          </template>

          <template #authors-cell="{ row }">
            <span v-if="row.original.authors.length" class="text-sm whitespace-normal">
              {{ formatAuthors(row.original.authors) }}
            </span>
            <UBadge v-else label="Not set" color="neutral" variant="subtle" size="sm" />
          </template>

          <template #doi-cell="{ row }">
            <a
              v-if="row.original.doi"
              :href="`https://doi.org/${row.original.doi}`"
              target="_blank"
              rel="noopener"
              class="text-sm text-primary"
              @click.stop
              >{{ row.original.doi }}</a
            >
            <UBadge v-else label="Not set" color="neutral" variant="subtle" size="sm" />
          </template>

          <template #year-cell="{ row }">
            <span v-if="row.original.year" class="text-sm">{{ row.original.year }}</span>
            <UBadge v-else label="Not set" color="neutral" variant="subtle" size="sm" />
          </template>

          <template #laboratory-cell="{ row }">
            <UBadge
              :label="row.original.laboratory?.laboratory_name ?? 'Unknown laboratory'"
              :color="isOwnLab(row.original) ? 'success' : 'neutral'"
              size="sm"
            />
          </template>

          <template #qc-cell="{ row }">
            <UBadge
              :label="reviewStatusOf(row.original.review_status).label"
              :color="reviewStatusOf(row.original.review_status).color"
              :variant="row.original.review_status === 'passed' ? 'solid' : 'subtle'"
              size="sm"
            />
          </template>

          <template #created_at-cell="{ row }">
            <span class="text-sm">{{
              new Date(row.original.created_at).toLocaleDateString()
            }}</span>
          </template>

          <template #actions-cell="{ row }">
            <UDropdownMenu :items="menuItems(row.original)" :content="{ align: 'end' }">
              <UButton
                icon="i-lucide-more-vertical"
                color="neutral"
                variant="ghost"
                size="sm"
                :aria-label="`Actions for ${row.original.title || 'study'}`"
              />
            </UDropdownMenu>
          </template>
        </UTable>
      </UContextMenu>
      <TablePagination
        v-model:page="view.page"
        v-model:page-size="view.pageSize"
        :total="view.total"
      />
    </div>

    <UModal
      v-model:open="showPurposeDialog"
      title="What would you like to do?"
      :ui="{ content: 'max-w-lg', footer: 'justify-end' }"
    >
      <template #body>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <UPageCard
            title="Plan a transfer experiment"
            description="Design a new experiment: describe it, plan its scenarios and print a checklist for the lab."
            icon="i-lucide-network"
            variant="outline"
            :on-click="() => choosePurpose('transfer')"
          />
          <UPageCard
            title="Add data to repository"
            description="Share an experiment you've carried out: describe it, plan its scenarios and enter the results."
            icon="i-lucide-database"
            variant="outline"
            :on-click="() => choosePurpose('repository')"
          />
        </div>
      </template>
      <template #footer>
        <UButton
          label="Cancel"
          icon="i-lucide-x"
          variant="ghost"
          @click="showPurposeDialog = false"
        />
      </template>
    </UModal>
  </div>
</template>
