<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useConfirm } from '@/composables/useConfirm'
import { useStudyReadOnly } from '@/composables/useStudyAccess'
import ScenarioViewDialog from './ScenarioViewDialog.vue'
import ScenarioFormDialog from './ScenarioFormDialog.vue'
import ScenarioDetails from './ScenarioDetails.vue'
import { listScenarios, getScenario, deleteScenario, updateScenario } from '@/api/scenarios'
import { listStudies } from '@/api/studies'
import type { Scenario, Study } from '@/api/types'
import type { ContextMenuItem, TableColumn, TableRow } from '@nuxt/ui'
import { manualSorting, searchRows, usePagination, useTableView } from '@/composables/useTableView'
import { sortHeader } from '@/composables/tableColumns'
import TableFilterDrawer from '@/components/ui/TableFilterDrawer.vue'
import TableLoadingSkeleton from '@/components/ui/TableLoadingSkeleton.vue'
import TablePagination from '@/components/ui/TablePagination.vue'

const props = defineProps<{ studyId: string }>()
// Fired after the study's scenarios were added, edited, deleted or unlinked.
const emit = defineEmits<{ changed: [] }>()

const confirm = useConfirm()
const readOnly = useStudyReadOnly()

const allScenarios = ref<Scenario[]>([])
const loading = ref(false)

const scenarios = computed(() =>
  allScenarios.value.filter((scenario) => scenario.studies.some((s) => s.id === props.studyId)),
)

const view = useTableView(scenarios, {
  searchFields: ['name', 'scenario_category.name'],
  filters: {
    name: { field: 'name' },
    category: { field: 'scenario_category.name' },
    realistic: { field: 'realistic', mode: 'equals' },
  },
  sortAccessors: { category: 'scenario_category.name' },
})

const columns = computed<TableColumn<Scenario>[]>(() => [
  { id: 'name', accessorKey: 'name', header: sortHeader('Name') },
  { id: 'category', header: sortHeader('Category') },
  { id: 'realistic', accessorKey: 'realistic', header: sortHeader('Realistic') },
  { id: 'shared', header: 'Shared' },
  { id: 'contact_templates', accessorKey: 'contact_templates', header: 'Contact templates' },
  { id: 'actions', header: '', meta: { class: { td: 'w-px' } } },
])

const realisticOptions = [
  { label: 'Realistic', value: true },
  { label: 'Not realistic', value: false },
]

async function load() {
  loading.value = true
  try {
    allScenarios.value = await listScenarios()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  load()
  restoreOpenDialogState()
})

async function onDelete(scenario: Scenario) {
  await deleteScenario(scenario.id)
  allScenarios.value = allScenarios.value.filter((s) => s.id !== scenario.id)
  emit('changed')
}

function onSaved() {
  load()
  emit('changed')
}

function confirmDelete(scenario: Scenario) {
  confirm.require({
    message: 'Delete this scenario permanently? This cannot be undone.',
    header: 'Delete scenario',
    rejectLabel: 'Cancel',
    acceptLabel: 'Delete',
    acceptColor: 'error',
    accept: () => onDelete(scenario),
  })
}

function scenarioLabel(scenario: Scenario): string {
  return scenario.name
}

// Bibliography-style citation (Author, A., Author, B. (Year). Title. Journal.)
// so studies can be told apart the way they'd appear in a reference list.
function citeStudy(study: Study): string {
  const authors = study.authors
    .map((author) => {
      const initials = author.first_name
        .split(/\s+/)
        .filter(Boolean)
        .map((part) => `${part[0]}.`)
        .join(' ')
      return [author.last_name, initials].filter(Boolean).join(', ')
    })
    .join(', ')

  const parts = [
    authors || null,
    study.year ? `(${study.year})` : null,
    study.title ?? `Study #${study.id}`,
    study.journal ?? null,
  ].filter(Boolean)

  return parts.join('. ')
}

// Only the study that originally created a scenario may edit it - other
// studies can only link/unlink it, since it's a shared record.
function isScenarioEditable(scenario: Scenario): boolean {
  if (readOnly.value) return false
  return scenario.owning_study_id == null || scenario.owning_study_id === props.studyId
}

// Deleting removes the scenario everywhere, so only the owning study may do
// it, and only once no other study still refers to it.
function isScenarioDeletable(scenario: Scenario): boolean {
  return isScenarioEditable(scenario) && scenario.studies.length <= 1
}

const formDialogVisible = ref(false)
const formDialogScenarioId = ref<string | null>(null)
const formDialogDuplicateFromId = ref<string | null>(null)

// Remembers which scenario dialog was open across a page reload, so an
// accidental refresh re-opens it instead of silently dropping back to the
// list (ScenarioFormDialog separately recovers the unsaved field values).
const openDialogStorageKey = computed(() => `transact.scenarioFormOpen.${props.studyId}`)

interface OpenDialogState {
  scenarioId: string | null
  duplicateFromId: string | null
}

function persistOpenDialogState() {
  try {
    if (!formDialogVisible.value) {
      localStorage.removeItem(openDialogStorageKey.value)
      return
    }
    const state: OpenDialogState = {
      scenarioId: formDialogScenarioId.value,
      duplicateFromId: formDialogDuplicateFromId.value,
    }
    localStorage.setItem(openDialogStorageKey.value, JSON.stringify(state))
  } catch {
    // Ignore - restoring the open dialog on reload is a convenience, not critical.
  }
}

function restoreOpenDialogState() {
  if (readOnly.value) return
  try {
    const raw = localStorage.getItem(openDialogStorageKey.value)
    if (!raw) return
    const state = JSON.parse(raw) as OpenDialogState
    formDialogScenarioId.value = state.scenarioId
    formDialogDuplicateFromId.value = state.duplicateFromId
    formDialogVisible.value = true
  } catch {
    // Ignore - if the stored state is corrupt, just stay on the list.
  }
}

// Covers every way the dialog can close (Cancel, successful save, Escape,
// backdrop click), not just the explicit open*Dialog() call sites.
watch(formDialogVisible, persistOpenDialogState)

function openAddDialog() {
  formDialogScenarioId.value = null
  formDialogDuplicateFromId.value = null
  formDialogVisible.value = true
}

function openEditDialog(scenario: Scenario) {
  formDialogScenarioId.value = scenario.id
  formDialogDuplicateFromId.value = null
  formDialogVisible.value = true
}

function onRowSelect(_event: Event, row: TableRow<Scenario>) {
  if (isScenarioEditable(row.original)) {
    openEditDialog(row.original)
  } else {
    openViewDialog(row.original)
  }
}

function menuItems(scenario: Scenario): ContextMenuItem[] {
  const items: ContextMenuItem[] = [
    {
      label: isScenarioEditable(scenario) ? 'Edit' : 'View',
      icon: isScenarioEditable(scenario) ? 'i-lucide-pencil' : 'i-lucide-eye',
      onSelect: () =>
        isScenarioEditable(scenario) ? openEditDialog(scenario) : openViewDialog(scenario),
    },
  ]
  if (!readOnly.value) {
    items.push({
      label: 'Duplicate',
      icon: 'i-lucide-copy-plus',
      onSelect: () => duplicateScenario(scenario),
    })
  }
  if (!readOnly.value && scenario.studies.length > 1) {
    items.push({
      label: 'Remove from this study',
      icon: 'i-lucide-x',
      onSelect: () => unlinkScenario(scenario),
    })
  }
  if (isScenarioDeletable(scenario)) {
    items.push({
      label: 'Delete',
      icon: 'i-lucide-trash-2',
      color: 'error',
      onSelect: () => confirmDelete(scenario),
    })
  }
  return items
}

// The right-clicked row's menu.
const contextMenuItems = ref<ContextMenuItem[]>([])

function onRowContextMenu(_event: Event, row: TableRow<Scenario>) {
  contextMenuItems.value = menuItems(row.original)
}

const viewDialogVisible = ref(false)
const viewedScenario = ref<Scenario | null>(null)
const viewLoading = ref(false)

async function openViewDialog(scenario: Scenario) {
  viewDialogVisible.value = true
  viewedScenario.value = null
  viewLoading.value = true
  try {
    viewedScenario.value = await getScenario(scenario.id)
  } finally {
    viewLoading.value = false
  }
}

// Reuses the same "Add scenario" form, pre-filled from the source scenario -
// same mechanism as duplicating from another study, just without the
// browse dialog since the source is already visible in this study's list.
function duplicateScenario(scenario: Scenario) {
  formDialogScenarioId.value = null
  formDialogDuplicateFromId.value = String(scenario.id)
  formDialogVisible.value = true
}

async function unlinkScenario(scenario: Scenario) {
  const studyIds = scenario.studies.map((s) => s.id).filter((id) => id !== props.studyId)
  const updated = await updateScenario(scenario.id, { study_ids: studyIds })
  allScenarios.value = allScenarios.value.map((s) => (s.id === updated.id ? updated : s))
  emit('changed')
}

// Duplicating a scenario from another study is browsed like a folder tree:
// a list of studies (cited bibliography-style) to drill into, then that
// study's scenarios, reviewed in full before the copy is actually created.
const allStudies = ref<Study[]>([])
const browseDialogVisible = ref(false)
const browseLevel = ref<'studies' | 'scenarios'>('studies')
const browsedStudy = ref<Study | null>(null)
const browseFilter = ref('')

const browsableStudies = computed(() =>
  allStudies.value.filter((study) => study.id !== props.studyId),
)

const browsedStudyScenarios = computed(() =>
  browsedStudy.value === null
    ? []
    : allScenarios.value.filter((scenario) =>
        scenario.studies.some((s) => s.id === browsedStudy.value?.id),
      ),
)

const visibleBrowsableStudies = computed(() =>
  searchRows(browsableStudies.value, ['title', 'journal', 'year', citeStudy], browseFilter.value),
)
const visibleBrowsedScenarios = computed(() =>
  searchRows(browsedStudyScenarios.value, ['name', 'scenario_category.name'], browseFilter.value),
)
const studyPages = usePagination(visibleBrowsableStudies, undefined, [browseFilter])
const browseScenarioPages = usePagination(visibleBrowsedScenarios, undefined, [browseFilter])
const studyColumns: TableColumn<Study>[] = [{ id: 'study', header: 'Study' }]
const browseScenarioColumns: TableColumn<Scenario>[] = [{ id: 'scenario', header: 'Scenario' }]

const browseBreadcrumbItems = computed(() => [
  { label: 'Studies', icon: 'i-lucide-folder', onClick: goToStudiesRoot },
  ...(browsedStudy.value ? [{ label: citeStudy(browsedStudy.value) }] : []),
])

async function openDuplicateFlow() {
  browseLevel.value = 'studies'
  browsedStudy.value = null
  browseFilter.value = ''
  previewedScenarioId.value = null
  previewedScenario.value = null
  browseDialogVisible.value = true
  if (!allStudies.value.length) {
    allStudies.value = await listStudies()
  }
}

function openStudyFolder(study: Study) {
  browsedStudy.value = study
  browseFilter.value = ''
  previewedScenarioId.value = null
  previewedScenario.value = null
  browseLevel.value = 'scenarios'
}

function goToStudiesRoot() {
  browsedStudy.value = null
  browseFilter.value = ''
  previewedScenarioId.value = null
  previewedScenario.value = null
  browseLevel.value = 'studies'
}

// The scenario preview is shown inline (next to the list) rather than in its
// own dialog, so switching between scenarios doesn't require closing and
// reopening a stacked dialog.
const previewedScenarioId = ref<string | null>(null)
const previewedScenario = ref<Scenario | null>(null)
const previewLoading = ref(false)

async function previewSourceScenario(scenario: Scenario) {
  previewedScenarioId.value = scenario.id
  previewedScenario.value = null
  previewLoading.value = true
  try {
    previewedScenario.value = await getScenario(scenario.id)
  } finally {
    previewLoading.value = false
  }
}

// Duplicating doesn't copy anything itself - it opens the normal "Add
// scenario" form pre-filled from the source scenario, so the copy is only
// actually created once the user reviews it and saves.
function confirmDuplicate() {
  if (!previewedScenario.value) return

  browseDialogVisible.value = false
  formDialogScenarioId.value = null
  formDialogDuplicateFromId.value = String(previewedScenario.value.id)
  formDialogVisible.value = true
}

defineExpose({ load })
</script>

<template>
  <div class="flex flex-col gap-6">
    <div v-if="!readOnly" class="flex items-center justify-end gap-2">
      <UButton
        data-tour="duplicate-scenario"
        label="Duplicate scenario from another study"
        icon="i-lucide-copy"
        variant="outline"
        @click="openDuplicateFlow"
      />
      <UButton
        data-tour="add-scenario"
        label="Add scenario"
        icon="i-lucide-plus"
        @click="openAddDialog"
      />
    </div>

    <div class="flex flex-col gap-3">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <UInput
          v-model="view.search"
          icon="i-lucide-search"
          placeholder="Keyword Search"
          class="w-full max-w-sm"
        />
        <TableFilterDrawer :active-count="view.activeFilterCount" @reset="view.resetFilters()">
          <UFormField label="Name">
            <UInput v-model="view.filters.name" placeholder="Search by name" class="w-full" />
          </UFormField>
          <UFormField label="Category">
            <UInput
              v-model="view.filters.category"
              placeholder="Search by category"
              class="w-full"
            />
          </UFormField>
          <UFormField label="Realistic">
            <USelectMenu
              v-model="view.filters.realistic"
              :items="realisticOptions"
              value-key="value"
              placeholder="Any"
              clear
              class="w-full"
            />
          </UFormField>
        </TableFilterDrawer>
      </div>

      <UContextMenu :items="contextMenuItems">
        <UTable
          v-model:sorting="view.sorting"
          :sorting-options="manualSorting"
          :data="view.rows"
          :columns="columns"
          :loading="loading"
          :get-row-id="(scenario: Scenario) => scenario.id"
          :on-select="onRowSelect"
          :on-contextmenu="onRowContextMenu"
          :ui="{ tr: 'cursor-pointer' }"
        >
          <template #loading>
            <TableLoadingSkeleton />
          </template>

          <template #empty>
            <div class="text-center text-surface-500 dark:text-surface-400 py-8">
              No scenarios yet.
            </div>
          </template>

          <template #category-cell="{ row }">
            <UBadge
              :label="row.original.scenario_category?.name ?? 'Uncategorized'"
              color="neutral"
            />
          </template>

          <template #realistic-cell="{ row }">
            <UBadge
              :label="row.original.realistic ? 'Realistic' : 'Not realistic'"
              :color="row.original.realistic ? 'success' : 'warning'"
            />
          </template>

          <template #shared-cell="{ row }">
            <UBadge
              v-if="row.original.studies.length > 1"
              :label="`${row.original.studies.length} studies`"
              color="info"
            />
            <span v-else class="text-sm text-surface-400 dark:text-surface-500">—</span>
          </template>

          <template #contact_templates-cell="{ row }">
            <span
              v-if="!row.original.contact_templates.length"
              class="text-sm text-surface-400 dark:text-surface-500"
              >—</span
            >
            <div v-else class="flex flex-wrap gap-1">
              <UBadge
                v-for="(contactTemplate, index) in row.original.contact_templates"
                :key="contactTemplate.id"
                :label="contactTemplate.name || `Contact template #${Number(index) + 1}`"
                color="neutral"
                variant="subtle"
              />
            </div>
          </template>

          <template #actions-cell="{ row }">
            <UDropdownMenu :items="menuItems(row.original)" :content="{ align: 'end' }">
              <UButton
                icon="i-lucide-more-vertical"
                aria-label="Actions"
                color="neutral"
                variant="ghost"
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

    <ScenarioViewDialog
      v-model:open="viewDialogVisible"
      :scenario="viewedScenario"
      :loading="viewLoading"
    />

    <ScenarioFormDialog
      v-model:open="formDialogVisible"
      :study-id="props.studyId"
      :id="formDialogScenarioId"
      :duplicate-from-id="formDialogDuplicateFromId"
      @saved="onSaved"
    />

    <UModal
      v-model:open="browseDialogVisible"
      title="Duplicate scenario from another study"
      :ui="{ content: 'max-w-5xl', footer: 'justify-end' }"
    >
      <template #body>
        <div class="flex flex-col gap-3">
          <UBreadcrumb :items="browseBreadcrumbItems" />
          <UInput
            v-model="browseFilter"
            type="text"
            icon="i-lucide-search"
            :placeholder="browseLevel === 'studies' ? 'Search studies' : 'Search scenarios'"
            class="w-full"
          />

          <div style="height: 28rem">
            <div v-if="browseLevel === 'studies'" class="flex h-full flex-col">
              <UTable
                :data="studyPages.rows"
                :columns="studyColumns"
                :get-row-id="(study: Study) => study.id"
                empty="No other studies found."
                sticky
                class="min-h-0 flex-1"
              >
                <template #study-cell="{ row }">
                  <button
                    type="button"
                    class="flex items-center gap-2 text-left w-full whitespace-normal hover:underline"
                    @click="openStudyFolder(row.original)"
                  >
                    <UIcon name="i-lucide-folder" class="size-4 shrink-0 text-dimmed" />
                    <span>{{ citeStudy(row.original) }}</span>
                  </button>
                </template>
              </UTable>
              <TablePagination
                v-model:page="studyPages.page"
                v-model:page-size="studyPages.pageSize"
                :total="studyPages.total"
              />
            </div>

            <div v-else class="flex gap-4 h-full">
              <div class="flex h-full w-64 shrink-0 flex-col">
                <UTable
                  :data="browseScenarioPages.rows"
                  :columns="browseScenarioColumns"
                  :get-row-id="(scenario: Scenario) => scenario.id"
                  empty="No scenarios in this study."
                  sticky
                  class="min-h-0 flex-1"
                >
                  <template #scenario-cell="{ row }">
                    <button
                      type="button"
                      class="flex items-center gap-2 text-left w-full hover:underline"
                      :class="{
                        'font-medium text-primary': previewedScenarioId === row.original.id,
                      }"
                      @click="previewSourceScenario(row.original)"
                    >
                      <UIcon name="i-lucide-file" class="size-4 shrink-0 text-dimmed" />
                      <span>{{ scenarioLabel(row.original) }}</span>
                    </button>
                  </template>
                </UTable>
                <TablePagination
                  v-model:page="browseScenarioPages.page"
                  v-model:page-size="browseScenarioPages.pageSize"
                  :total="browseScenarioPages.total"
                />
              </div>

              <div
                class="flex-1 min-w-0 border-l border-surface-200 dark:border-surface-700 pl-4 overflow-y-auto h-full"
              >
                <div
                  v-if="previewedScenarioId === null"
                  class="flex items-center justify-center h-full text-sm text-surface-500 dark:text-surface-400"
                >
                  Select a scenario to preview it.
                </div>
                <ScenarioDetails v-else :scenario="previewedScenario" :loading="previewLoading" />
              </div>
            </div>
          </div>
        </div>
      </template>
      <template #footer>
        <UButton
          label="Close"
          icon="i-lucide-x"
          variant="ghost"
          @click="browseDialogVisible = false"
        />
        <UButton
          label="Continue with this scenario"
          trailing-icon="i-lucide-arrow-right"
          icon="i-lucide-copy-plus"
          :disabled="!previewedScenario"
          @click="confirmDuplicate"
        />
      </template>
    </UModal>
  </div>
</template>
