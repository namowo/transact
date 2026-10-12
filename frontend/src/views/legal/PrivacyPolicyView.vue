<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useSiteSettingsStore } from '@/stores/siteSettings'

const siteSettings = useSiteSettingsStore()

onMounted(async () => {
  await siteSettings.load()
  const settings = siteSettings.settings
  if (settings?.privacy_policy_mode === 'url' && settings.privacy_policy_url) {
    window.location.href = settings.privacy_policy_url
  }
})

const isRedirecting = computed(
  () =>
    siteSettings.settings?.privacy_policy_mode === 'url' &&
    !!siteSettings.settings.privacy_policy_url,
)
</script>

<template>
  <div class="flex flex-col gap-4">
    <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Privacy Policy</h1>

    <p v-if="siteSettings.loading" class="text-sm text-muted">Loading…</p>

    <p v-else-if="isRedirecting" class="text-sm text-muted">
      Redirecting to
      <a :href="siteSettings.settings!.privacy_policy_url!" class="text-primary">{{
        siteSettings.settings!.privacy_policy_url
      }}</a>
    </p>

    <div
      v-else-if="siteSettings.settings?.privacy_policy_text"
      class="legal-content text-surface-700 dark:text-surface-200"
      v-html="siteSettings.settings.privacy_policy_text"
    />

    <p v-else class="text-sm text-muted">No privacy policy has been set up yet.</p>
  </div>
</template>
