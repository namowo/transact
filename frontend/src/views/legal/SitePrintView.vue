<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useSiteSettingsStore } from '@/stores/siteSettings'

const siteSettings = useSiteSettingsStore()

onMounted(async () => {
  await siteSettings.load()
  const settings = siteSettings.settings
  if (settings?.site_print_mode === 'url' && settings.site_print_url) {
    window.location.href = settings.site_print_url
  }
})

const isRedirecting = computed(
  () =>
    siteSettings.settings?.site_print_mode === 'url' && !!siteSettings.settings.site_print_url,
)
</script>

<template>
  <div class="flex flex-col gap-4">
    <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Site Print</h1>

    <p v-if="siteSettings.loading" class="text-sm text-muted">Loading…</p>

    <p v-else-if="isRedirecting" class="text-sm text-muted">
      Redirecting to
      <a :href="siteSettings.settings!.site_print_url!" class="text-primary">{{
        siteSettings.settings!.site_print_url
      }}</a>
    </p>

    <div
      v-else-if="siteSettings.settings?.site_print_text"
      class="legal-content text-surface-700 dark:text-surface-200"
      v-html="siteSettings.settings.site_print_text"
    />

    <p v-else class="text-sm text-muted">No Site Print has been set up yet.</p>
  </div>
</template>
