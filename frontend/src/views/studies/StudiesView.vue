<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import ContextMenu from 'openvue/contextmenu'
import { FilterMatchMode } from '@openvue/core/api'
import { listStudies } from '@/api/studies'
import { useAuthStore } from '@/stores/auth'
import type { Study } from '@/api/types'
import type { MenuItem } from 'openvue/menuitem'

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

const qcStatusOptions = [
  { label: 'Passed', value: true },
  { label: 'Not checked', value: false },
]

function initFilters() {
  return {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
    title: { value: null, matchMode: FilterMatchMode.CONTAINS },
    year: { value: null, matchMode: FilterMatchMode.CONTAINS },
    'laboratory.laboratory_name': { value: null, matchMode: FilterMatchMode.CONTAINS },
    quality_check_passed: { value: null, matchMode: FilterMatchMode.EQUALS },
  }
}

const filters = ref(initFilters())

function clearFilters() {
  filters.value = initFilters()
}

function isOwnLab(study: Study) {
  return study.laboratory_id === auth.user?.laboratory_id
}

function canEdit(study: Study) {
  return !!auth.user && (auth.user.is_superuser || isOwnLab(study))
}

function openStep(study: Study, step: 'details' | 'planning' | 'data-entry') {
  router.push({ name: 'studies-edit', params: { id: study.id }, query: { step } })
}

const showPurposeDialog = ref(false)

function choosePurpose(purpose: 'transfer' | 'repository') {
  showPurposeDialog.value = false
  router.push({ name: 'studies-new', query: { purpose } })
}

const contextMenu = ref<InstanceType<typeof ContextMenu>>()
const selectedStudy = ref<Study>()

const contextMenuItems = computed<MenuItem[]>(() => {
  const study = selectedStudy.value
  if (!study) return []

  const editable = canEdit(study)

  return [
    {
      label: 'Details',
      icon: 'i-lucide-pencil',
      disabled: !editable,
      command: () => openStep(study, 'details'),
    },
    {
      label: 'Planning',
      icon: 'i-lucide-network',
      disabled: !editable,
      command: () => openStep(study, 'planning'),
    },
    {
      label: 'Add data',
      icon: 'i-lucide-database',
      visible: !!study.add_data_to_repository,
      disabled: !editable,
      command: () => openStep(study, 'data-entry'),
    },
    {
      separator: true,
    },
    {
      // TODO: enable once study data export is implemented
      label: 'Download (coming soon)',
      icon: 'i-lucide-download',
      disabled: true,
    },
  ]
})

function onRowContextMenu(event: { originalEvent: Event; data: Study }) {
  selectedStudy.value = event.data
  contextMenu.value?.show(event.originalEvent)
}

function openContextMenu(event: Event, study: Study) {
  selectedStudy.value = study
  contextMenu.value?.show(event)
}

function onRowClick(event: { data: Study }) {
  if (!canEdit(event.data)) return
  openStep(event.data, 'details')
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
                ? 'Studies from all laboratories. You can only edit studies from your own laboratory.'
                : 'Published studies from all laboratories.'
          }}
        </p>
      </div>
      <UButton
        v-if="auth.isAuthenticated"
        label="Add study"
        icon="i-lucide-plus"
        @click="showPurposeDialog = true"
      />
    </div>

    <div class="flex flex-col gap-3">
      <div class="flex items-center justify-between gap-3">
        <UButton type="button" icon="i-lucide-filter-x" variant="outline" size="sm" @click="clearFilters()">
          Clear Filters
        </UButton>
        <UInput
          v-model="filters['global'].value"
          type="text"
          icon="i-lucide-search"
          placeholder="Search title, author, journal, DOI…"
          class="sm:max-w-sm w-full"
        />
      </div>

      <ContextMenu ref="contextMenu" :model="contextMenuItems" />

      <div class="overflow-x-auto">
      <DataTable
        v-model:filters="filters"
        v-model:context-menu-selection="selectedStudy"
        :value="scopedStudies"
        :loading="loading"
        data-key="id"
        context-menu
        removableSort
        paginator
        :rows="10"
        :rows-per-page-options="[10, 25, 50]"
        :global-filter-fields="['title', 'journal', 'doi', 'year']"
        filter-display="menu"
        sort-field="created_at"
        :sort-order="-1"
        :row-class="(data: Study) => (canEdit(data) ? 'cursor-pointer hover:bg-elevated' : '')"
        @row-contextmenu="onRowContextMenu"
        @row-click="onRowClick"
      >
        <template #empty>No studies found.</template>

        <Column
          field="title"
          header="Title"
          sortable
          :show-filter-operator="false"
          :show-add-button="false"
        >
          <template #body="{ data }: { data: Study }">
            <span v-if="data.title" class="font-medium">{{ data.title }}</span>
            <UBadge v-else label="Not set" color="neutral" variant="subtle" size="sm" />
          </template>
          <template #filter="{ filterModel }">
            <UInput v-model="filterModel.value" type="text" placeholder="Search by title" />
          </template>
        </Column>

        <Column header="Authors">
          <template #body="{ data }: { data: Study }">
            <span v-if="data.authors.length" class="text-sm">{{ formatAuthors(data.authors) }}</span>
            <UBadge v-else label="Not set" color="neutral" variant="subtle" size="sm" />
          </template>
        </Column>

        <Column header="DOI" style="width: 10rem">
          <template #body="{ data }: { data: Study }">
            <a
              v-if="data.doi"
              :href="`https://doi.org/${data.doi}`"
              target="_blank"
              rel="noopener"
              class="text-sm text-primary"
              @click.stop
              >{{ data.doi }}</a
            >
            <UBadge v-else label="Not set" color="neutral" variant="subtle" size="sm" />
          </template>
        </Column>

        <Column
          field="year"
          header="Year"
          sortable
          style="width: 6rem"
          :show-filter-operator="false"
          :show-add-button="false"
        >
          <template #body="{ data }: { data: Study }">
            <span v-if="data.year" class="text-sm">{{ data.year }}</span>
            <UBadge v-else label="Not set" color="neutral" variant="subtle" size="sm" />
          </template>
          <template #filter="{ filterModel }">
            <UInput v-model="filterModel.value" type="text" placeholder="Search by year" />
          </template>
        </Column>

        <Column
          field="laboratory.laboratory_name"
          header="Laboratory"
          sortable
          style="width: 12rem"
          :show-filter-operator="false"
          :show-add-button="false"
        >
          <template #body="{ data }: { data: Study }">
            <UBadge
              :label="data.laboratory?.laboratory_name ?? 'Unknown laboratory'"
              :color="isOwnLab(data) ? 'success' : 'neutral'"
              size="sm"
            />
          </template>
          <template #filter="{ filterModel }">
            <UInput v-model="filterModel.value" type="text" placeholder="Search by laboratory" />
          </template>
        </Column>

        <Column
          field="quality_check_passed"
          header="QC"
          style="width: 8rem"
          :show-filter-match-modes="false"
          :show-filter-operator="false"
          :show-add-button="false"
        >
          <template #body="{ data }: { data: Study }">
            <UBadge
              :label="data.quality_check_passed ? 'Passed' : 'Not checked'"
              :color="data.quality_check_passed ? 'info' : 'neutral'"
              :variant="data.quality_check_passed ? 'solid' : 'subtle'"
              size="sm"
            />
          </template>
          <template #filter="{ filterModel }">
            <USelectMenu
              v-model="filterModel.value"
              :items="qcStatusOptions"
              value-key="value"
              placeholder="Any status"
              clear
              class="w-full"
            />
          </template>
        </Column>

        <Column field="created_at" header="Created" sortable style="width: 8rem">
          <template #body="{ data }: { data: Study }">
            <span class="text-sm">{{ new Date(data.created_at).toLocaleDateString() }}</span>
          </template>
        </Column>

        <Column v-if="auth.isAuthenticated" header="" style="width: 3rem">
          <template #body="{ data }: { data: Study }">
            <UButton
              icon="i-lucide-more-vertical"
              color="neutral"
              variant="ghost"
              size="sm"
              @click.stop="openContextMenu($event, data)"
            />
          </template>
        </Column>
      </DataTable>
      </div>
    </div>

    <UModal
      v-model:open="showPurposeDialog"
      title="What would you like to do?"
      :ui="{ content: 'max-w-lg', footer: 'justify-end' }"
    >
      <template #body>
      <div class="flex flex-col sm:flex-row gap-3">
        <UButton
          label="Plan a transfer experiment"
          icon="i-lucide-network"
          class="flex-1"
          @click="choosePurpose('transfer')"
        />
        <UButton
          label="Add data to repository"
          icon="i-lucide-database"
          class="flex-1"
          @click="choosePurpose('repository')"
        />
      </div>
      </template>
      <template #footer>
        <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="showPurposeDialog = false" />
      </template>
    </UModal>
  </div>
</template>
