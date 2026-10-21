<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import ContextMenu from 'openvue/contextmenu'
import type { MenuItem } from 'openvue/menuitem'
import { FilterMatchMode } from '@openvue/core/api'
import { useConfirm } from '@/composables/useConfirm'
import ScenarioViewDialog from './ScenarioViewDialog.vue'
import ScenarioFormDialog from './ScenarioFormDialog.vue'
import ScenarioDetails from './ScenarioDetails.vue'
import { listScenarios, getScenario, deleteScenario, updateScenario } from '@/api/scenarios'
import { listStudies } from '@/api/studies'
import type { Scenario, Study } from '@/api/types'

const props = defineProps<{ studyId: string }>()

const confirm = useConfirm()

const allScenarios = ref<Scenario[]>([])
const loading = ref(false)

const scenarios = computed(() =>
  allScenarios.value.filter((scenario) => scenario.studies.some((s) => s.id === props.studyId)),
)

function initFilters() {
  return {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
    'scenario_category.name': { value: null, matchMode: FilterMatchMode.CONTAINS },
    realistic: { value: null, matchMode: FilterMatchMode.EQUALS },
  }
}

const filters = ref(initFilters())

function clearFilters() {
  filters.value = initFilters()
}

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
  return `${scenario.scenario_category?.name ?? 'Uncategorized'} — Scenario #${scenario.id}`
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

function onRowClick(event: { data: Scenario }) {
  if (isScenarioEditable(event.data)) {
    openEditDialog(event.data)
  } else {
    openViewDialog(event.data)
  }
}

const contextMenu = ref<InstanceType<typeof ContextMenu>>()
const selectedScenario = ref<Scenario>()

const contextMenuItems = computed<MenuItem[]>(() => {
  const scenario = selectedScenario.value
  if (!scenario) return []

  return [
    {
      label: isScenarioEditable(scenario) ? 'Edit' : 'View',
      icon: isScenarioEditable(scenario) ? 'i-lucide-pencil' : 'i-lucide-eye',
      command: () =>
        isScenarioEditable(scenario) ? openEditDialog(scenario) : openViewDialog(scenario),
    },
    {
      label: 'Remove from this study',
      icon: 'i-lucide-x',
      visible: scenario.studies.length > 1,
      command: () => unlinkScenario(scenario),
    },
    {
      label: 'Delete',
      icon: 'i-lucide-trash-2',
      visible: isScenarioDeletable(scenario),
      command: () => confirmDelete(scenario),
    },
  ]
})

function onRowContextMenu(event: { originalEvent: Event; data: Scenario }) {
  selectedScenario.value = event.data
  contextMenu.value?.show(event.originalEvent)
}

function openContextMenu(event: Event, scenario: Scenario) {
  selectedScenario.value = scenario
  contextMenu.value?.show(event)
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

async function unlinkScenario(scenario: Scenario) {
  const studyIds = scenario.studies.map((s) => s.id).filter((id) => id !== props.studyId)
  const updated = await updateScenario(scenario.id, { study_ids: studyIds })
  allScenarios.value = allScenarios.value.map((s) => (s.id === updated.id ? updated : s))
}

// Duplicating a scenario from another study is browsed like a folder tree:
// a list of studies (cited bibliography-style) to drill into, then that
// study's scenarios, reviewed in full before the copy is actually created.
const allStudies = ref<Study[]>([])
const browseDialogVisible = ref(false)
const browseLevel = ref<'studies' | 'scenarios'>('studies')
const browsedStudy = ref<Study | null>(null)
const browseFilter = ref('')

const browsableStudies = computed(() => allStudies.value.filter((study) => study.id !== props.studyId))

const browsedStudyScenarios = computed(() =>
  browsedStudy.value === null
    ? []
    : allScenarios.value.filter((scenario) =>
        scenario.studies.some((s) => s.id === browsedStudy.value?.id),
      ),
)

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
    <div class="flex items-center justify-end gap-2">
      <UButton
        label="Duplicate scenario from another study"
        icon="i-lucide-copy"
        variant="outline"
        @click="openDuplicateFlow"
      />
      <UButton
        label="Add scenario"
        icon="i-lucide-plus"
        @click="openAddDialog"
      />
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <UProgress class="w-12" />
    </div>

    <div v-else class="overflow-x-auto">
      <ContextMenu ref="contextMenu" :model="contextMenuItems" />

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
        :value="scenarios"
        data-key="id"
        filterDisplay="menu"
        removableSort
        :globalFilterFields="['scenario_category.name']"
        :row-class="() => 'cursor-pointer hover:bg-elevated'"
        @row-click="onRowClick"
        @row-contextmenu="onRowContextMenu"
      >
        <template #empty>
          <div class="text-center text-surface-500 dark:text-surface-400 py-8">No scenarios yet.</div>
        </template>

        <Column
          field="scenario_category.name"
          header="Category"
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #body="{ data }">
            <UBadge :label="data.scenario_category?.name ?? 'Uncategorized'" color="neutral" />
          </template>
          <template #filter="{ filterModel }">
            <UInput v-model="filterModel.value" type="text" placeholder="Search by category" />
          </template>
        </Column>

        <Column
          field="realistic"
          header="Realistic"
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
          :showFilterMatchModes="false"
        >
          <template #body="{ data }">
            <UBadge
              :label="data.realistic ? 'Realistic' : 'Not realistic'"
              :color="data.realistic ? 'success' : 'warning'"
            />
          </template>
          <template #filter="{ filterModel }">
            <USelectMenu
              v-model="filterModel.value"
              :items="[
                { label: 'Realistic', value: true },
                { label: 'Not realistic', value: false },
              ]"
              label-key="label"
              value-key="value"
              placeholder="Any"
              clear
              class="w-full"
            />
          </template>
        </Column>

        <Column header="Shared">
          <template #body="{ data }">
            <UBadge
              v-if="data.studies.length > 1"
              :label="`${data.studies.length} studies`"
              color="info"
            />
            <span v-else class="text-sm text-surface-400 dark:text-surface-500">—</span>
          </template>
        </Column>

        <Column header="Contact templates">
          <template #body="{ data }">
            {{ data.contact_templates.length }}
          </template>
        </Column>

        <Column header="" style="width: 1%">
          <template #body="{ data }">
            <UButton
              icon="i-lucide-more-vertical"
              aria-label="Actions"
              color="neutral"
              variant="ghost"
              @click.stop="openContextMenu($event, data)"
            />
          </template>
        </Column>
      </DataTable>
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
      @saved="load"
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
          <DataTable
            v-if="browseLevel === 'studies'"
            :value="browsableStudies"
            :globalFilterFields="['title', 'journal', 'year']"
            :filters="{ global: { value: browseFilter, matchMode: 'contains' } }"
            dataKey="id"
            scrollable
            scrollHeight="28rem"
          >
            <template #empty>No other studies found.</template>
            <Column header="Study">
              <template #body="{ data }">
                <button
                  type="button"
                  class="flex items-center gap-2 text-left w-full hover:underline"
                  @click="openStudyFolder(data)"
                >
                  <i class="pi pi-folder text-surface-400" />
                  <span>{{ citeStudy(data) }}</span>
                </button>
              </template>
            </Column>
          </DataTable>

          <div v-else class="flex gap-4 h-full">
            <DataTable
              :value="browsedStudyScenarios"
              :globalFilterFields="['scenario_category.name']"
              :filters="{ global: { value: browseFilter, matchMode: 'contains' } }"
              dataKey="id"
              scrollable
              scrollHeight="28rem"
              class="w-64 shrink-0"
            >
              <template #empty>No scenarios in this study.</template>
              <Column header="Scenario">
                <template #body="{ data }">
                  <button
                    type="button"
                    class="flex items-center gap-2 text-left w-full hover:underline"
                    :class="{ 'font-medium text-primary': previewedScenarioId === data.id }"
                    @click="previewSourceScenario(data)"
                  >
                    <i class="pi pi-file text-surface-400" />
                    <span>{{ scenarioLabel(data) }}</span>
                  </button>
                </template>
              </Column>
            </DataTable>

            <div class="flex-1 min-w-0 border-l border-surface-200 dark:border-surface-700 pl-4 overflow-y-auto h-full">
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
        <UButton label="Close" icon="i-lucide-x" variant="ghost" @click="browseDialogVisible = false" />
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
