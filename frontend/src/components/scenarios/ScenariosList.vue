<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import DataView from 'primevue/dataview'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'
import Breadcrumb from 'primevue/breadcrumb'
import { useConfirm } from 'primevue/useconfirm'
import ProgressSpinner from 'primevue/progressspinner'
import ScenarioViewDialog from './ScenarioViewDialog.vue'
import ScenarioDetails from './ScenarioDetails.vue'
import { listScenarios, getScenario, deleteScenario, updateScenario } from '@/api/scenarios'
import { listStudies } from '@/api/studies'
import type { Scenario, Study } from '@/api/types'

const props = defineProps<{ studyId: string }>()

const router = useRouter()
const confirm = useConfirm()

const allScenarios = ref<Scenario[]>([])
const loading = ref(false)

const scenarios = computed(() =>
  allScenarios.value.filter((scenario) => scenario.studies.some((s) => s.id === props.studyId)),
)

async function load() {
  loading.value = true
  try {
    allScenarios.value = await listScenarios()
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function onDelete(scenario: Scenario) {
  await deleteScenario(scenario.id)
  allScenarios.value = allScenarios.value.filter((s) => s.id !== scenario.id)
}

function confirmDelete(scenario: Scenario) {
  confirm.require({
    message: 'Delete this scenario permanently? This cannot be undone.',
    header: 'Delete scenario',
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: 'Cancel', severity: 'secondary', text: true },
    acceptProps: { label: 'Delete', severity: 'danger' },
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
  router.push({
    name: 'scenarios-new',
    params: { studyId: props.studyId },
    query: { duplicateFrom: String(previewedScenario.value.id) },
  })
}

defineExpose({ load })
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-end gap-2">
      <Button
        label="Duplicate scenario from another study"
        icon="pi pi-copy"
        outlined
        @click="openDuplicateFlow"
      />
      <Button
        label="Add scenario"
        icon="pi pi-plus"
        @click="router.push({ name: 'scenarios-new', params: { studyId: props.studyId } })"
      />
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <ProgressSpinner style="width: 3rem; height: 3rem" />
    </div>

    <DataView v-else :value="scenarios" data-key="id">
      <template #empty>
        <div class="text-center text-surface-500 dark:text-surface-400 py-8">No scenarios yet.</div>
      </template>

      <template #list="slotProps">
        <div class="flex flex-col">
          <div
            v-for="(item, index) in slotProps.items as Scenario[]"
            :key="item.id"
            class="flex flex-col sm:flex-row sm:items-start p-6 gap-4"
            :class="{ 'border-t border-surface-200 dark:border-surface-700': index !== 0 }"
          >
            <div class="flex-1 flex flex-col gap-2">
              <div class="flex flex-wrap items-center gap-2">
                <Tag
                  :value="item.scenario_category?.name ?? 'Uncategorized'"
                  severity="secondary"
                />
                <Tag
                  :value="item.realistic ? 'Realistic' : 'Not realistic'"
                  :severity="item.realistic ? 'success' : 'warn'"
                />
                <Tag
                  v-if="item.studies.length > 1"
                  :value="`Shared across ${item.studies.length} studies`"
                  severity="info"
                />
              </div>
              <div class="text-sm text-surface-500 dark:text-surface-400">
                {{ item.contact_templates.length }} contact template{{
                  item.contact_templates.length === 1 ? '' : 's'
                }}
              </div>
            </div>
            <div class="flex flex-row sm:flex-col gap-2 shrink-0">
              <Button
                v-if="isScenarioEditable(item)"
                label="Edit"
                icon="pi pi-pencil"
                severity="secondary"
                outlined
                @click="
                  router.push({
                    name: 'scenarios-edit',
                    params: { studyId: props.studyId, id: item.id },
                  })
                "
              />
              <Button
                v-else
                label="View"
                icon="pi pi-eye"
                severity="secondary"
                outlined
                @click="openViewDialog(item)"
              />
              <Button
                v-if="item.studies.length > 1"
                label="Remove from this study"
                icon="pi pi-times"
                severity="warn"
                outlined
                @click="unlinkScenario(item)"
              />
              <Button
                v-if="isScenarioDeletable(item)"
                label="Delete"
                icon="pi pi-trash"
                severity="danger"
                outlined
                @click="confirmDelete(item)"
              />
            </div>
          </div>
        </div>
      </template>
    </DataView>

    <ScenarioViewDialog
      v-model:visible="viewDialogVisible"
      :scenario="viewedScenario"
      :loading="viewLoading"
    />

    <Dialog
      v-model:visible="browseDialogVisible"
      header="Duplicate scenario from another study"
      modal
      position="top"
      :style="{ width: '64rem' }"
    >
      <div class="flex flex-col gap-3">
        <Breadcrumb
          :home="{ label: 'Studies', icon: 'pi pi-folder', command: goToStudiesRoot }"
          :model="browseBreadcrumbItems"
        />
        <IconField iconPosition="left">
          <InputIcon class="pi pi-search" />
          <InputText
            v-model="browseFilter"
            type="text"
            :placeholder="browseLevel === 'studies' ? 'Search studies' : 'Search scenarios'"
            fluid
          />
        </IconField>

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
      <template #footer>
        <Button label="Close" text @click="browseDialogVisible = false" />
        <Button
          label="Continue with this scenario"
          icon="pi pi-arrow-right"
          icon-pos="right"
          :disabled="!previewedScenario"
          @click="confirmDuplicate"
        />
      </template>
    </Dialog>
  </div>
</template>
