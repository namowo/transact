<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import DataView from 'primevue/dataview'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import ProgressSpinner from 'primevue/progressspinner'
import { listScenarios, deleteScenario } from '@/api/scenarios'
import type { Scenario } from '@/api/types'

const props = defineProps<{ studyId: number }>()

const router = useRouter()

const scenarios = ref<Scenario[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const allScenarios = await listScenarios()
    scenarios.value = allScenarios.filter((scenario) => scenario.study_id === props.studyId)
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function onDelete(scenario: Scenario) {
  await deleteScenario(scenario.id)
  scenarios.value = scenarios.value.filter((s) => s.id !== scenario.id)
}

defineExpose({ load })
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-end">
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
              </div>
              <div class="text-sm text-surface-500 dark:text-surface-400">
                {{ item.contacts.length }} contact{{ item.contacts.length === 1 ? '' : 's' }}
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
  </div>
</template>
