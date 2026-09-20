<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import PersistenceDetails from './PersistenceDetails.vue'
import { persistenceLabel } from './persistenceDraft'
import type { Persistence, Scenario } from '@/api/types'

const props = defineProps<{
  scenarios: Scenario[]
}>()

const emit = defineEmits<{
  select: [persistence: Persistence]
}>()

const visible = defineModel<boolean>('visible', { default: false })

const level = ref<'scenarios' | 'persistencies'>('scenarios')
const browsedScenario = ref<Scenario | null>(null)
const filter = ref('')
const previewedId = ref<string | null>(null)

watch(visible, (isVisible) => {
  if (isVisible) {
    level.value = 'scenarios'
    browsedScenario.value = null
    filter.value = ''
    previewedId.value = null
  }
})

function scenarioLabel(scenario: Scenario): string {
  return `${scenario.scenario_category?.name ?? 'Uncategorized'} — Scenario #${scenario.id}`
}

function openScenarioFolder(scenario: Scenario) {
  browsedScenario.value = scenario
  filter.value = ''
  previewedId.value = null
  level.value = 'persistencies'
}

function goToScenariosRoot() {
  browsedScenario.value = null
  filter.value = ''
  previewedId.value = null
  level.value = 'scenarios'
}

const breadcrumbItems = computed(() => [
  { label: 'Scenarios', icon: 'i-lucide-folder', onClick: goToScenariosRoot },
  ...(browsedScenario.value ? [{ label: scenarioLabel(browsedScenario.value) }] : []),
])

const browsedScenarioPersistencies = computed(() => browsedScenario.value?.persistencies ?? [])

function previewedPersistence(): Persistence | null {
  return browsedScenarioPersistencies.value.find((p) => p.id === previewedId.value) ?? null
}

function confirmSelection() {
  const persistence = previewedPersistence()
  if (!persistence) return
  emit('select', persistence)
  visible.value = false
}
</script>

<template>
  <!-- TODO: dialog position (was position="top") - UModal has no built-in top-aligned position -->
  <UModal
    v-model:open="visible"
    title="Duplicate a persistence from this study"
    :ui="{ content: 'max-w-5xl' }"
  >
    <template #body>
      <div class="flex flex-col gap-3">
        <UBreadcrumb :items="breadcrumbItems" />
        <UInput
          v-model="filter"
          type="text"
          icon="i-lucide-search"
          :placeholder="level === 'scenarios' ? 'Search scenarios' : 'Search persistencies'"
          class="w-full"
        />

        <div style="height: 28rem">
          <DataTable
            v-if="level === 'scenarios'"
            :value="scenarios"
            :globalFilterFields="['scenario_category.name']"
            :filters="{ global: { value: filter, matchMode: 'contains' } }"
            dataKey="id"
            scrollable
            scrollHeight="28rem"
          >
            <template #empty>No scenarios in this study yet.</template>
            <Column header="Scenario">
              <template #body="{ data }">
                <button
                  type="button"
                  class="flex items-center gap-2 text-left w-full hover:underline"
                  @click="openScenarioFolder(data)"
                >
                  <i class="pi pi-folder text-surface-400" />
                  <span>{{ scenarioLabel(data) }}</span>
                </button>
              </template>
            </Column>
          </DataTable>

          <div v-else class="flex gap-4 h-full">
            <DataTable
              :value="browsedScenarioPersistencies"
              :globalFilterFields="['name', 'disturbance_category.name', 'geographic_location_category.name']"
              :filters="{ global: { value: filter, matchMode: 'contains' } }"
              dataKey="id"
              scrollable
              scrollHeight="28rem"
              class="w-72 shrink-0"
            >
              <template #empty>No persistencies on this scenario.</template>
              <Column header="Persistence">
                <template #body="{ data }">
                  <button
                    type="button"
                    class="flex items-center gap-2 text-left w-full hover:underline"
                    :class="{ 'font-medium text-primary': previewedId === data.id }"
                    @click="previewedId = data.id"
                  >
                    <i class="pi pi-file text-surface-400" />
                    <span>{{ persistenceLabel(data) }}</span>
                  </button>
                </template>
              </Column>
            </DataTable>

            <div class="flex-1 min-w-0 border-l border-surface-200 dark:border-surface-700 pl-4 overflow-y-auto h-full">
              <div
                v-if="previewedId === null"
                class="flex items-center justify-center h-full text-sm text-surface-500 dark:text-surface-400"
              >
                Select a persistence to preview it.
              </div>
              <PersistenceDetails v-else :persistence="previewedPersistence()" />
            </div>
          </div>
        </div>
      </div>
    </template>
    <template #footer>
      <UButton label="Close" variant="ghost" @click="visible = false" />
      <UButton
        label="Duplicate into this scenario"
        trailing-icon="i-lucide-arrow-right"
        :disabled="previewedId === null"
        @click="confirmSelection"
      />
    </template>
  </UModal>
</template>
