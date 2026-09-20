<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import DataView from 'primevue/dataview'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import { useConfirm } from '@/composables/useConfirm'
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
      <UButton
        label="Duplicate scenario from another study"
        icon="i-lucide-copy"
        variant="outline"
        @click="openDuplicateFlow"
      />
      <UButton
        label="Add scenario"
        icon="i-lucide-plus"
        @click="router.push({ name: 'scenarios-new', params: { studyId: props.studyId } })"
      />
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <UProgress class="w-12" />
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
                <UBadge
                  :label="item.scenario_category?.name ?? 'Uncategorized'"
                  color="neutral"
                />
                <UBadge
                  :label="item.realistic ? 'Realistic' : 'Not realistic'"
                  :color="item.realistic ? 'success' : 'warning'"
                />
                <UBadge
                  v-if="item.studies.length > 1"
                  :label="`Shared across ${item.studies.length} studies`"
                  color="info"
                />
              </div>
              <div class="text-sm text-surface-500 dark:text-surface-400">
                {{ item.contact_templates.length }} contact template{{
                  item.contact_templates.length === 1 ? '' : 's'
                }}
              </div>
            </div>
            <div class="flex flex-row sm:flex-col gap-2 shrink-0">
              <UButton
                v-if="isScenarioEditable(item)"
                label="Edit"
                icon="i-lucide-pencil"
                color="neutral"
                variant="outline"
                @click="
                  router.push({
                    name: 'scenarios-edit',
                    params: { studyId: props.studyId, id: item.id },
                  })
                "
              />
              <UButton
                v-else
                label="View"
                icon="i-lucide-eye"
                color="neutral"
                variant="outline"
                @click="openViewDialog(item)"
              />
              <UButton
                v-if="item.studies.length > 1"
                label="Remove from this study"
                icon="i-lucide-x"
                color="warning"
                variant="outline"
                @click="unlinkScenario(item)"
              />
              <UButton
                v-if="isScenarioDeletable(item)"
                label="Delete"
                icon="i-lucide-trash-2"
                color="error"
                variant="outline"
                @click="confirmDelete(item)"
              />
            </div>
          </div>
        </div>
      </template>
    </DataView>

    <ScenarioViewDialog
      v-model:open="viewDialogVisible"
      :scenario="viewedScenario"
      :loading="viewLoading"
    />

    <UModal
      v-model:open="browseDialogVisible"
      title="Duplicate scenario from another study"
      :ui="{ content: 'max-w-5xl' }"
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
        <UButton label="Close" variant="ghost" @click="browseDialogVisible = false" />
        <UButton
          label="Continue with this scenario"
          trailing-icon="i-lucide-arrow-right"
          :disabled="!previewedScenario"
          @click="confirmDuplicate"
        />
      </template>
    </UModal>
  </div>
</template>
