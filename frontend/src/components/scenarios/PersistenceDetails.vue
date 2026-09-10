<script setup lang="ts">
import type { Persistence } from '@/api/types'

const props = defineProps<{
  persistence: Persistence | null
}>()

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
  <div v-if="persistence" class="flex flex-col gap-3 text-sm">
    <span class="font-semibold">{{ persistence.name || `Persistence #${persistence.id}` }}</span>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2">
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
        <span class="font-medium">Disturbance:</span> {{ persistence.disturbance_category.name }}
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
</template>
