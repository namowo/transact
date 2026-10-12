<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { listStudies } from '@/api/studies'
import type { Study } from '@/api/types'

const studies = ref<Study[]>([])
const statsLoading = ref(false)

onMounted(async () => {
  statsLoading.value = true
  studies.value = await listStudies().catch(() => [])
  statsLoading.value = false
})

const publishedCount = computed(() => studies.value.filter((s) => s.published).length)
const labCount = computed(
  () => new Set(studies.value.map((s) => s.laboratory_id).filter(Boolean)).size,
)

const stats = computed(() => [
  { label: 'Studies in the repository', value: studies.value.length, icon: 'i-lucide-book-open' },
  { label: 'Contributing laboratories', value: labCount.value, icon: 'i-lucide-building-2' },
  { label: 'Published datasets', value: publishedCount.value, icon: 'i-lucide-globe' },
])

const features = [
  {
    icon: 'i-lucide-database',
    title: 'Open, structured data',
    body: 'Record raw data from transfer experiments in a standardized, internationally comparable format.',
  },
  {
    icon: 'i-lucide-flask-conical',
    title: 'Standardized experiments',
    body: 'Characterize non-transfer-related variability and establish comparability between laboratories.',
  },
  {
    icon: 'i-lucide-scale',
    title: 'Built for forensic science',
    body: 'Lays the groundwork for reliable probability estimates in activity-level crime scene reconstruction.',
  },
]
</script>

<template>
  <div class="flex flex-col gap-10">
    <!-- Hero -->
    <div
      class="relative overflow-hidden rounded-2xl border border-default bg-linear-to-br from-primary-50 to-elevated/40 dark:from-primary-950/40 dark:to-elevated/40 px-6 py-10 sm:px-10 sm:py-14"
    >
      <div class="relative flex flex-col items-center text-center gap-5 max-w-2xl mx-auto">
        <div class="flex items-center gap-3">
          <img src="/transact_logo_dark.png" alt="TransAct" class="size-10 dark:hidden" />
          <img
            src="/transact_logo_light.png"
            alt="TransAct"
            class="size-10 hidden dark:block"
          />
          <span class="text-lg font-bold tracking-tight text-surface-900 dark:text-surface-0"
            >TransAct</span
          >
        </div>

        <h1 class="text-3xl sm:text-4xl font-extrabold tracking-tight text-surface-900 dark:text-surface-0">
          The open data platform for forensic nucleic acid transfer research
        </h1>

        <p class="text-surface-600 dark:text-surface-300 text-base sm:text-lg">
          TransAct helps forensic molecular biology laboratories record, standardize, and share
          raw DNA/RNA transfer data — building the evidence base for activity-level crime scene
          reconstruction.
        </p>

        <div class="flex flex-wrap items-center justify-center gap-3 mt-1">
          <UButton label="Create an account" icon="i-lucide-user-plus" size="lg" :to="{ name: 'register' }" />
          <UButton
            label="Log in"
            icon="i-lucide-log-in"
            size="lg"
            color="neutral"
            variant="outline"
            :to="{ name: 'login' }"
          />
          <UButton
            label="Browse studies"
            icon="i-lucide-book-open"
            size="lg"
            color="neutral"
            variant="ghost"
            :to="{ name: 'studies-all' }"
          />
          <UButton
            label="Documentation"
            icon="i-lucide-file-text"
            size="lg"
            color="neutral"
            variant="ghost"
            :to="{ name: 'docs' }"
          />
        </div>
      </div>
    </div>

    <!-- Live stats -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <UCard v-for="stat in stats" :key="stat.label">
        <div class="flex items-center gap-4">
          <div
            class="flex items-center justify-center size-11 rounded-lg bg-primary/10 text-primary shrink-0"
          >
            <UIcon :name="stat.icon" class="size-6" />
          </div>
          <div class="min-w-0">
            <p class="text-2xl font-bold text-surface-900 dark:text-surface-0">
              {{ statsLoading ? '–' : stat.value }}
            </p>
            <p class="text-sm text-surface-500 truncate">{{ stat.label }}</p>
          </div>
        </div>
      </UCard>
    </div>

    <!-- What TransAct does -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <UCard v-for="feature in features" :key="feature.title">
        <div class="flex flex-col gap-2">
          <UIcon :name="feature.icon" class="size-6 text-primary" />
          <h3 class="font-semibold text-surface-900 dark:text-surface-0">{{ feature.title }}</h3>
          <p class="text-sm text-surface-500">{{ feature.body }}</p>
        </div>
      </UCard>
    </div>
  </div>
</template>
