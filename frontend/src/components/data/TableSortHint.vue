<script setup lang="ts">
// Shows the multi-sort modifier key of the viewer's operating system; if it
// can't be told, both keys are named.
type Platform = 'mac' | 'other' | 'unknown'

function detectPlatform(): Platform {
  if (typeof navigator === 'undefined') return 'unknown'
  const nav = navigator as Navigator & { userAgentData?: { platform?: string } }
  const platform = nav.userAgentData?.platform || nav.platform || nav.userAgent || ''
  if (!platform) return 'unknown'
  return /mac|iphone|ipad|ipod/i.test(platform) ? 'mac' : 'other'
}

const platform = detectPlatform()
</script>

<template>
  <p class="flex items-start gap-1.5 text-xs text-muted">
    <UIcon name="i-lucide-arrow-up-down" class="size-3.5 shrink-0 mt-px" />
    <span>
      Click a column header to sort by it. Hold
      <UKbd v-if="platform === 'mac'" value="⌘" size="sm" />
      <UKbd v-else-if="platform === 'other'" value="Ctrl" size="sm" />
      <template v-else><UKbd value="Ctrl" size="sm" /> (Windows/Linux) or <UKbd value="⌘" size="sm" /> (macOS)</template>
      while clicking further headers to sort by several columns - the numbers on the headers show their order. Your
      sort is saved for all studies and also used for the CSV download.
    </span>
  </p>
</template>
