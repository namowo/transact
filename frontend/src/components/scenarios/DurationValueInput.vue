<script setup lang="ts">
import { ref, watch } from 'vue'
import InputNumber from 'primevue/inputnumber'
import InputGroup from 'primevue/inputgroup'
import InputGroupAddon from 'primevue/inputgroupaddon'

// The underlying v-model is always seconds. The UI splits it into
// years/days/hours/minutes/seconds fields so composite durations (e.g. "1
// year, 10 days, 10:10:10") can be entered directly, since a persistence
// interval or disturbance duration can range from seconds to years.
const seconds = defineModel<number | null>({ default: null })

defineProps<{ invalid?: boolean }>()

const units = [
  { key: 'years', label: 'y', factor: 31536000 },
  { key: 'days', label: 'd', factor: 86400 },
  { key: 'hours', label: 'h', factor: 3600 },
  { key: 'minutes', label: 'min', factor: 60 },
  { key: 'seconds', label: 's', factor: 1 },
] as const

const parts = ref<Record<(typeof units)[number]['key'], number | null>>({
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
      for (const { key } of units) parts.value[key] = null
      return
    }
    let remainder = value
    for (const { key, factor } of units) {
      const amount = Math.trunc(remainder / factor)
      parts.value[key] = amount === 0 ? null : amount
      remainder -= amount * factor
    }
  },
  { immediate: true },
)

function onPartChange() {
  syncing = true
  const total = units.reduce((sum, { key, factor }) => sum + (parts.value[key] ?? 0) * factor, 0)
  const anySet = units.some(({ key }) => parts.value[key] != null)
  seconds.value = anySet ? total : null
  syncing = false
}
</script>

<template>
  <div class="flex flex-wrap gap-2">
    <InputGroup v-for="{ key, label } in units" :key="key" class="flex-1 min-w-24">
      <InputNumber
        v-model="parts[key]"
        :min="0"
        :invalid="invalid"
        fluid
        @update:model-value="onPartChange"
      />
      <InputGroupAddon>{{ label }}</InputGroupAddon>
    </InputGroup>
  </div>
</template>
