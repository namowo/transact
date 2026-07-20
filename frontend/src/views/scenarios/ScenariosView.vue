<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getStudy } from '@/api/studies'
import ScenariosList from '@/components/scenarios/ScenariosList.vue'
import type { Study } from '@/api/types'

const props = defineProps<{ studyId: string }>()

const studyId = computed(() => Number(props.studyId))
const study = ref<Study | null>(null)

onMounted(async () => {
  study.value = await getStudy(studyId.value)
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Scenarios</h1>
      <p v-if="study" class="text-surface-500 dark:text-surface-400 text-sm mt-1">
        {{ study.title }}
      </p>
    </div>

    <ScenariosList :study-id="studyId" />
  </div>
</template>
