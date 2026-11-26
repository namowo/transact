<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { TableColumn } from '@nuxt/ui'
import { searchRows, usePagination } from '@/composables/useTableView'
import PersistenceDetails from './PersistenceDetails.vue'
import { persistenceLabel } from './persistenceDraft'
import type { Persistence, Scenario } from '@/api/types'
import TablePagination from '@/components/ui/TablePagination.vue'

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
  return scenario.name
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

const visibleScenarios = computed(() =>
  searchRows(props.scenarios, ['scenario_category.name', scenarioLabel], filter.value),
)
const visiblePersistencies = computed(() =>
  searchRows(
    browsedScenarioPersistencies.value,
    ['name', 'geographic_location_category.name', persistenceLabel],
    filter.value,
  ),
)

const scenarioPages = usePagination(visibleScenarios, undefined, [filter])
const persistencePages = usePagination(visiblePersistencies, undefined, [filter])

const scenarioColumns: TableColumn<Scenario>[] = [{ id: 'scenario', header: 'Scenario' }]
const persistenceColumns: TableColumn<Persistence>[] = [
  { id: 'persistence', header: 'Persistence' },
]

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
    :ui="{ content: 'max-w-5xl', footer: 'justify-end' }"
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
          <div v-if="level === 'scenarios'" class="flex h-full flex-col">
            <UTable
              :data="scenarioPages.rows"
              :columns="scenarioColumns"
              :get-row-id="(scenario: Scenario) => scenario.id"
              empty="No scenarios in this study yet."
              sticky
              class="min-h-0 flex-1"
            >
              <template #scenario-cell="{ row }">
                <button
                  type="button"
                  class="flex items-center gap-2 text-left w-full hover:underline"
                  @click="openScenarioFolder(row.original)"
                >
                  <UIcon name="i-lucide-folder" class="size-4 shrink-0 text-dimmed" />
                  <span>{{ scenarioLabel(row.original) }}</span>
                </button>
              </template>
            </UTable>
            <TablePagination
              v-model:page="scenarioPages.page"
              v-model:page-size="scenarioPages.pageSize"
              :total="scenarioPages.total"
            />
          </div>

          <div v-else class="flex gap-4 h-full">
            <div class="flex h-full w-72 shrink-0 flex-col">
              <UTable
                :data="persistencePages.rows"
                :columns="persistenceColumns"
                :get-row-id="(persistence: Persistence) => persistence.id"
                empty="No persistencies on this scenario."
                sticky
                class="min-h-0 flex-1"
              >
                <template #persistence-cell="{ row }">
                  <button
                    type="button"
                    class="flex items-center gap-2 text-left w-full hover:underline"
                    :class="{ 'font-medium text-primary': previewedId === row.original.id }"
                    @click="previewedId = row.original.id"
                  >
                    <UIcon name="i-lucide-file" class="size-4 shrink-0 text-dimmed" />
                    <span>{{ persistenceLabel(row.original) }}</span>
                  </button>
                </template>
              </UTable>
              <TablePagination
                v-model:page="persistencePages.page"
                v-model:page-size="persistencePages.pageSize"
                :total="persistencePages.total"
              />
            </div>

            <div
              class="flex-1 min-w-0 border-l border-surface-200 dark:border-surface-700 pl-4 overflow-y-auto h-full"
            >
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
      <UButton label="Close" icon="i-lucide-x" variant="ghost" @click="visible = false" />
      <UButton
        label="Duplicate into this scenario"
        trailing-icon="i-lucide-arrow-right"
        icon="i-lucide-copy-plus"
        :disabled="previewedId === null"
        @click="confirmSelection"
      />
    </template>
  </UModal>
</template>
