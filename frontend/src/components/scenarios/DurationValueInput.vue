<script setup lang="ts">
import { computed, ref, watch } from 'vue'

// The underlying v-model is always seconds. The UI splits it into
// years/days/hours/minutes/seconds fields so composite durations (e.g. "1
// year, 10 days, 10:10:10") can be entered directly, since a persistence
// interval or disturbance duration can range from seconds to years.
const seconds = defineModel<number | null>({ default: null })

const props = defineProps<{
  invalid?: boolean
  // Restrict which unit fields are shown (e.g. ['hours', 'minutes']). Defaults
  // to all units, for durations that can range from seconds to years.
  units?: Array<AllUnits[number]['key']>
}>()

const allUnits = [
  { key: 'years', label: 'y', factor: 31536000 },
  { key: 'days', label: 'd', factor: 86400 },
  { key: 'hours', label: 'h', factor: 3600 },
  { key: 'minutes', label: 'min', factor: 60 },
  { key: 'seconds', label: 's', factor: 1 },
] as const

type AllUnits = typeof allUnits

const activeUnits = computed(() =>
  props.units ? allUnits.filter(({ key }) => props.units!.includes(key)) : allUnits,
)

const parts = ref<Record<AllUnits[number]['key'], number | null>>({
  years: null,
  days: null,
  hours: null,
  minutes: null,
  seconds: null,
})

let syncing = false

watch(
  seconds,
  (value) => {
    if (syncing) return
    if (value == null) {
      for (const { key } of allUnits) parts.value[key] = null
      return
    }
    let remainder = value
    for (const { key, factor } of activeUnits.value) {
      const amount = Math.trunc(remainder / factor)
      parts.value[key] = amount === 0 ? null : amount
      remainder -= amount * factor
    }
  },
  { immediate: true },
)

function onPartChange() {
  syncing = true
  const total = activeUnits.value.reduce(
    (sum, { key, factor }) => sum + (parts.value[key] ?? 0) * factor,
    0,
  )
  const anySet = activeUnits.value.some(({ key }) => parts.value[key] != null)
  seconds.value = anySet ? total : null
  syncing = false
}
</script>

<template>
  <div class="flex flex-wrap gap-2">
    <UFieldGroup v-for="{ key, label } in activeUnits" :key="key" class="flex-1 min-w-24">
      <UInputNumber
        v-model="parts[key]"
        :min="0"
        :color="invalid ? 'error' : undefined"
        orientation="vertical"
        class="w-full"
        @update:model-value="onPartChange"
      />
      <UBadge color="neutral" variant="outline" size="lg" :label="label" />
    </UFieldGroup>
  </div>
</template>
