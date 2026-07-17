<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Card from 'primevue/card'
import { defaultDocSlug, docPages, fallbackDocPage } from '@/data/docs'

const route = useRoute()

const page = computed(() => {
  const slug = (route.params.slug as string | undefined) ?? defaultDocSlug
  return docPages.find((p) => p.slug === slug) ?? fallbackDocPage
})
</script>

<template>
  <Card>
    <template #title>{{ page.title }}</template>
    <template #content>
      <p class="text-surface-700 dark:text-surface-200">{{ page.body }}</p>
    </template>
  </Card>
</template>
