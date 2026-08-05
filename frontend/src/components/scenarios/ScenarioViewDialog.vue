<script setup lang="ts">
import { computed } from 'vue'
import Dialog from 'primevue/dialog'
import Tag from 'primevue/tag'
import ProgressSpinner from 'primevue/progressspinner'
import Message from 'primevue/message'
import Divider from 'primevue/divider'
import { persistenceLabel } from './persistenceDraft'
import type { Scenario } from '@/api/types'

const props = defineProps<{
  scenario: Scenario | null
  loading: boolean
}>()

const visible = defineModel<boolean>('visible', { default: false })

const title = computed(() =>
  props.scenario ? `${props.scenario.scenario_category?.name ?? 'Uncategorized'} — Scenario #${props.scenario.id}` : 'Scenario',
)

function formatDuration(seconds: number | null | undefined): string | null {
  if (seconds == null) return null
  const units: [string, number][] = [
    ['y', 31536000],
    ['d', 86400],
    ['h', 3600],
    ['min', 60],
    ['s', 1],
  ]
  const parts: string[] = []
  let remainder = seconds
  for (const [label, factor] of units) {
    const amount = Math.trunc(remainder / factor)
    if (amount > 0) parts.push(`${amount}${label}`)
    remainder -= amount * factor
  }
  return parts.length ? parts.join(' ') : '0s'
}
</script>

<template>
  <Dialog v-model:visible="visible" :header="title" modal :style="{ width: '40rem' }">
    <div v-if="loading" class="flex justify-center py-12">
      <ProgressSpinner style="width: 3rem; height: 3rem" />
    </div>

    <div v-else-if="scenario" class="flex flex-col gap-6 text-sm">
      <div class="flex flex-wrap items-center gap-2">
        <Tag
          :value="scenario.realistic ? 'Realistic' : 'Not realistic'"
          :severity="scenario.realistic ? 'success' : 'warn'"
        />
        <Tag
          v-if="scenario.studies.length > 1"
          :value="`Shared across ${scenario.studies.length} studies`"
          severity="info"
        />
      </div>

      <div>
        <h4 class="font-medium mb-2">
          Persistence{{ scenario.persistencies.length === 1 ? '' : 's' }}
          ({{ scenario.persistencies.length }})
        </h4>
        <p v-if="!scenario.persistencies.length" class="text-surface-500 dark:text-surface-400">
          None linked.
        </p>
        <div v-else class="flex flex-col gap-4">
          <div
            v-for="persistence in scenario.persistencies"
            :key="persistence.id"
            class="flex flex-col gap-1 border border-surface-200 dark:border-surface-700 rounded-md p-3"
          >
            <span class="font-medium">{{ persistenceLabel(persistence) }}</span>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1 text-surface-600 dark:text-surface-300">
              <div v-if="persistence.interval_of_persistence != null">
                <span class="font-medium">Interval of persistence:</span>
                {{ formatDuration(persistence.interval_of_persistence) }}
              </div>
              <div v-if="persistence.temperature != null">
                <span class="font-medium">Temperature:</span> {{ persistence.temperature }} °C
              </div>
              <div v-if="persistence.humidity != null">
                <span class="font-medium">Humidity:</span> {{ persistence.humidity }} %
              </div>
              <div v-if="persistence.uv_irradiation != null">
                <span class="font-medium">UV irradiation:</span> {{ persistence.uv_irradiation }} mW/cm²
              </div>
              <div v-if="persistence.duration_of_disturbance != null">
                <span class="font-medium">Duration of disturbance:</span>
                {{ formatDuration(persistence.duration_of_disturbance) }}
              </div>
              <div v-if="persistence.indoors">Indoors</div>
              <div v-if="persistence.change_over_time">Changes over time</div>
              <div v-if="persistence.disturbance_category">
                <span class="font-medium">Disturbance:</span>
                {{ persistence.disturbance_category.name }}
              </div>
              <div v-if="persistence.geographic_location_category">
                <span class="font-medium">Geographic location:</span>
                {{ persistence.geographic_location_category.name }}
              </div>
            </div>
            <p v-if="persistence.description_of_disturbance" class="text-surface-500 dark:text-surface-400">
              {{ persistence.description_of_disturbance }}
            </p>
          </div>
        </div>
      </div>

      <Divider class="m-0" />

      <div>
        <h4 class="font-medium mb-2">
          Contact template{{ scenario.contact_templates.length === 1 ? '' : 's' }}
          ({{ scenario.contact_templates.length }})
        </h4>
        <p v-if="!scenario.contact_templates.length" class="text-surface-500 dark:text-surface-400">
          None linked.
        </p>
        <div v-else class="flex flex-col gap-4">
          <div
            v-for="(contactTemplate, index) in scenario.contact_templates"
            :key="contactTemplate.id"
            class="flex flex-col gap-1 border border-surface-200 dark:border-surface-700 rounded-md p-3"
          >
            <span class="font-medium">Contact template #{{ index + 1 }}</span>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1 text-surface-600 dark:text-surface-300">
              <div v-if="contactTemplate.duration != null">
                <span class="font-medium">Duration:</span>
                {{ formatDuration(contactTemplate.duration) }}
              </div>
              <div v-if="contactTemplate.contact_area != null">
                <span class="font-medium">Contact area:</span> {{ contactTemplate.contact_area }} cm²
              </div>
              <div v-if="contactTemplate.temperature != null">
                <span class="font-medium">Temperature:</span> {{ contactTemplate.temperature }} °C
              </div>
              <div v-if="contactTemplate.humidity != null">
                <span class="font-medium">Humidity:</span> {{ contactTemplate.humidity }} %
              </div>
              <div v-if="contactTemplate.uv_irradiation != null">
                <span class="font-medium">UV irradiation:</span> {{ contactTemplate.uv_irradiation }} mW/cm²
              </div>
              <div v-if="contactTemplate.activity_category">
                <span class="font-medium">Activity:</span> {{ contactTemplate.activity_category.name }}
              </div>
              <div v-if="contactTemplate.pressure_estimate">
                <span class="font-medium">Pressure estimate:</span> {{ contactTemplate.pressure_estimate.name }}
              </div>
              <div v-if="contactTemplate.friction_applied_estimate">
                <span class="font-medium">Friction applied estimate:</span>
                {{ contactTemplate.friction_applied_estimate.name }}
              </div>
            </div>
            <p v-if="contactTemplate.description_of_contact" class="text-surface-500 dark:text-surface-400">
              {{ contactTemplate.description_of_contact }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <Message v-else severity="error" size="small">Could not load this scenario.</Message>
  </Dialog>
</template>
