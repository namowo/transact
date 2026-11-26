<script setup lang="ts">
import type { PrivacyPolicy } from '@/api/types'

defineProps<{
  policy: PrivacyPolicy
}>()
</script>

<template>
  <div
    v-if="policy.mode === 'text'"
    class="legal-content text-surface-700 dark:text-surface-200"
    v-html="policy.text"
  />
  <p v-else class="text-sm">
    The privacy policy is published at
    <a :href="policy.url ?? undefined" target="_blank" rel="noopener" class="text-primary hover:underline">{{
      policy.url
    }}</a>.
  </p>
</template>
