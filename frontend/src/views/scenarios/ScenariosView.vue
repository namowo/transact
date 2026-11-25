<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getStudy } from '@/api/studies'
import ScenariosList from '@/components/scenarios/ScenariosList.vue'
import { canEnterStudyData, provideStudyReadOnly } from '@/composables/useStudyAccess'
import { useAuthStore } from '@/stores/auth'
import type { Study } from '@/api/types'

const props = defineProps<{ studyId: string }>()

const studyId = computed(() => props.studyId)
const study = ref<Study | null>(null)
const auth = useAuthStore()

provideStudyReadOnly(computed(() => !!study.value && !canEnterStudyData(study.value, auth.user)))

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

    <ScenariosList v-if="study" :study-id="studyId" />
  </div>
</template>
