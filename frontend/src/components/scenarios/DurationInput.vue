<script setup lang="ts">
import { ref, watch } from 'vue'
import InputText from 'primevue/inputtext'

// The underlying v-model is always seconds. The text field accepts either a
// plain (possibly fractional) number of hours, "H:MM" for hours+minutes, or
// "H:MM:SS" for hours+minutes+seconds - the colon count picks the format.
const seconds = defineModel<number | null>({ default: null })

const text = ref('')
let syncing = false

watch(
  seconds,
  (value) => {
    if (syncing) return
    text.value = value == null ? '' : formatSeconds(value)
  },
  { immediate: true },
)

function formatSeconds(value: number): string {
  if (value % 3600 === 0) {
    return String(value / 3600)
  }
  const hours = Math.trunc(value / 3600)
  const minutes = Math.trunc((value % 3600) / 60)
  const secs = Math.trunc(value % 60)
  return secs === 0
    ? `${hours}:${String(minutes).padStart(2, '0')}`
    : `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
}

function parseDuration(input: string): number | null {
  const trimmed = input.trim()
  if (!trimmed) return null

  const parts = trimmed.split(':')
  if (parts.some((part) => part.trim() === '' || Number.isNaN(Number(part)))) return null

  if (parts.length === 1) {
    return Number(parts[0]) * 3600
  }
  if (parts.length === 2) {
    return Number(parts[0]) * 3600 + Number(parts[1]) * 60
  }
  if (parts.length === 3) {
    return Number(parts[0]) * 3600 + Number(parts[1]) * 60 + Number(parts[2])
  }
  return null
}

function onInput() {
  syncing = true
  seconds.value = parseDuration(text.value)
  syncing = false
}
</script>

<template>
  <div class="flex flex-col gap-1">
    <InputText
      v-model="text"
      placeholder="e.g. 2 or 2:30 or 2:30:15"
      fluid
      @update:model-value="onInput"
    />
    <span class="text-sm text-surface-500 dark:text-surface-400">
      Enter hours (e.g. 2), hours:minutes (2:30), or hours:minutes:seconds (2:30:15).
    </span>
  </div>
</template>
