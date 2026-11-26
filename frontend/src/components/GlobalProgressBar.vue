<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { isGlobalLoading } from '@/composables/useGlobalLoading'

// Wait this long before showing the bar, so fast requests don't flash it.
const SHOW_DELAY_MS = 150
const TRICKLE_INTERVAL_MS = 250
const FADE_OUT_MS = 300

const progress = ref(0)
const visible = ref(false)

let showTimer: ReturnType<typeof setTimeout> | undefined
let hideTimer: ReturnType<typeof setTimeout> | undefined
let trickleTimer: ReturnType<typeof setInterval> | undefined

function clearTimers() {
  clearTimeout(showTimer)
  clearTimeout(hideTimer)
  clearInterval(trickleTimer)
}

function start() {
  clearTimers()
  if (visible.value) {
    trickle()
    return
  }
  showTimer = setTimeout(() => {
    progress.value = 10
    visible.value = true
    trickle()
  }, SHOW_DELAY_MS)
}

// Creeps towards 90 % without ever reaching it, as the real duration is unknown.
function trickle() {
  trickleTimer = setInterval(() => {
    progress.value += (90 - progress.value) * 0.1
  }, TRICKLE_INTERVAL_MS)
}

function finish() {
  clearTimers()
  if (!visible.value) return
  progress.value = 100
  hideTimer = setTimeout(() => {
    visible.value = false
    hideTimer = setTimeout(() => (progress.value = 0), FADE_OUT_MS)
  }, 200)
}

watch(isGlobalLoading, (loading) => (loading ? start() : finish()), { immediate: true })

onBeforeUnmount(clearTimers)
</script>

<template>
  <UProgress
    :model-value="progress"
    size="2xs"
    role="progressbar"
    :aria-hidden="!visible"
    class="pointer-events-none transition-opacity duration-300"
    :class="visible ? 'opacity-100' : 'opacity-0'"
    :ui="{ base: 'h-0.5 rounded-none bg-transparent', indicator: 'rounded-none' }"
  />
</template>
