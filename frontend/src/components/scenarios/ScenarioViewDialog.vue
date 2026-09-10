<script setup lang="ts">
import { computed } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
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

const visible = defineModel<boolean>('visible', { default: false })

const title = computed(() =>
  props.scenario ? `${props.scenario.scenario_category?.name ?? 'Uncategorized'} — Scenario #${props.scenario.id}` : 'Scenario',
)
</script>

<template>
  <Dialog v-model:visible="visible" :header="title" modal :style="{ width: '40rem' }">
    <ScenarioDetails :scenario="scenario" :loading="loading" />

    <template v-if="confirmLabel" #footer>
      <Button label="Cancel" text @click="visible = false" />
      <Button
        :label="confirmLabel"
        :loading="confirmLoading"
        :disabled="!scenario"
        @click="emit('confirm')"
      />
    </template>
  </Dialog>
</template>
