<script setup lang="ts">
import { computed } from 'vue'
import ScenarioDetails from './ScenarioDetails.vue'
import type { Scenario } from '@/api/types'

const props = defineProps<{
  scenario: Scenario | null
  loading: boolean
  confirmLabel?: string
  confirmLoading?: boolean
}>()

const emit = defineEmits<{
  confirm: []
}>()

const open = defineModel<boolean>('open', { default: false })

const title = computed(() =>
  props.scenario ? `${props.scenario.scenario_category?.name ?? 'Uncategorized'} — Scenario #${props.scenario.id}` : 'Scenario',
)
</script>

<template>
  <UModal v-model:open="open" :title="title" :ui="{ content: 'max-w-2xl' }">
    <template #body>
      <ScenarioDetails :scenario="scenario" :loading="loading" />
    </template>

    <template v-if="confirmLabel" #footer>
      <UButton label="Cancel" variant="ghost" @click="open = false" />
      <UButton
        :label="confirmLabel"
        :loading="confirmLoading"
        :disabled="!scenario"
        @click="emit('confirm')"
      />
    </template>
  </UModal>
</template>
