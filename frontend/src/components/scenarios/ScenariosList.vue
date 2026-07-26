<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import DataView from 'primevue/dataview'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import ProgressSpinner from 'primevue/progressspinner'
import EntitySelect from './EntitySelect.vue'
import { listScenarios, deleteScenario, updateScenario } from '@/api/scenarios'
import type { Scenario } from '@/api/types'

const props = defineProps<{ studyId: number }>()

const router = useRouter()

const allScenarios = ref<Scenario[]>([])
const loading = ref(false)

const scenarios = computed(() =>
  allScenarios.value.filter((scenario) => scenario.studies.some((s) => s.id === props.studyId)),
)

// Scenarios not yet linked to this study, offered in the "Add existing
// scenario" dialog - a scenario may belong to many studies.
const linkableScenarios = computed(() =>
  allScenarios.value.filter((scenario) => !scenario.studies.some((s) => s.id === props.studyId)),
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

function scenarioLabel(scenario: Scenario): string {
  return `${scenario.scenario_category?.name ?? 'Uncategorized'} — Scenario #${scenario.id}`
}

const linkDialogVisible = ref(false)
const scenarioToLink = ref<number | null>(null)
const linking = ref(false)

function openLinkDialog() {
  scenarioToLink.value = null
  linkDialogVisible.value = true
}

async function linkScenario() {
  if (scenarioToLink.value === null) return
  const scenario = allScenarios.value.find((s) => s.id === scenarioToLink.value)
  if (!scenario) return

  linking.value = true
  try {
    const studyIds = [...scenario.studies.map((s) => s.id), props.studyId]
    const updated = await updateScenario(scenario.id, { study_ids: studyIds })
    allScenarios.value = allScenarios.value.map((s) => (s.id === updated.id ? updated : s))
    linkDialogVisible.value = false
  } finally {
    linking.value = false
  }
}

async function unlinkScenario(scenario: Scenario) {
  const studyIds = scenario.studies.map((s) => s.id).filter((id) => id !== props.studyId)
  const updated = await updateScenario(scenario.id, { study_ids: studyIds })
  allScenarios.value = allScenarios.value.map((s) => (s.id === updated.id ? updated : s))
}

defineExpose({ load })
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-end gap-2">
      <Button
        label="Add existing scenario"
        icon="pi pi-link"
        outlined
        :disabled="!linkableScenarios.length"
        @click="openLinkDialog"
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
                v-if="item.studies.length > 1"
                label="Remove from this study"
                icon="pi pi-times"
                severity="warn"
                outlined
                @click="unlinkScenario(item)"
              />
              <Button
                label="Delete"
                icon="pi pi-trash"
                severity="danger"
                outlined
                @click="onDelete(item)"
              />
            </div>
          </div>
        </div>
      </template>
    </DataView>

    <Dialog
      v-model:visible="linkDialogVisible"
      header="Add existing scenario"
      modal
      :style="{ width: '28rem' }"
    >
      <div class="flex flex-col gap-4">
        <EntitySelect
          v-model="scenarioToLink"
          label="Scenario"
          :options="linkableScenarios"
          :option-label="scenarioLabel"
        />
      </div>
      <template #footer>
        <Button label="Cancel" text @click="linkDialogVisible = false" />
        <Button
          label="Add"
          :loading="linking"
          :disabled="scenarioToLink === null"
          @click="linkScenario"
        />
      </template>
    </Dialog>
  </div>
</template>
