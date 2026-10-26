<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getStudy } from '@/api/studies'
import type { Study } from '@/api/types'

const props = defineProps<{ id: string }>()

const router = useRouter()

const study = ref<Study | null>(null)
const loading = ref(true)
const loadError = ref('')

onMounted(async () => {
  try {
    study.value = await getStudy(props.id)
  } catch {
    loadError.value = 'Could not load this study.'
  } finally {
    loading.value = false
  }
})

function onBack() {
  router.push({ name: 'studies-edit', params: { id: props.id }, query: { step: 'planning' } })
}

function onPrint() {
  window.print()
}

// Generic checklist sections to fill in by hand - not generated from the
// study's data, since that varies too much per study to template well.
// Each item is just a label; the page itself provides the writing space.
const sections: { title: string; items: string[] }[] = [
  {
    title: 'Ethics',
    items: [
      'Ethics approval obtained / application submitted',
      'Informed consent form prepared',
      'Data protection / privacy assessment completed',
    ],
  },
  {
    title: 'Instructions for participants',
    items: [
      'Written instructions drafted',
      'Instructions reviewed by a second person',
      'Instructions translated, if needed',
    ],
  },
  {
    title: 'Data to collect from individuals',
    items: [
      'Demographic information (age, sex, etc.)',
      'Relevant habits/behaviour (e.g. handwashing, activity before sampling)',
      'Consent and withdrawal documentation',
    ],
  },
  {
    title: 'Timeline',
    items: [
      'Recruitment period',
      'Sampling date(s)',
      'Analysis/processing deadline',
    ],
  },
  {
    title: 'Similar studies',
    items: [
      'Literature search for comparable scenarios completed',
      'Relevant studies listed and reviewed',
    ],
  },
]
</script>

<template>
  <div id="print-area" class="flex flex-col gap-6 p-6 max-w-3xl mx-auto print:p-0 print:max-w-none">
    <div class="flex items-center justify-between print:hidden">
      <UButton
        label="Back to study"
        icon="i-lucide-arrow-left"
        variant="ghost"
        size="sm"
        class="-ml-3!"
        @click="onBack"
      />
      <UButton label="Print" icon="i-lucide-printer" @click="onPrint" />
    </div>

    <div v-if="loading" class="flex justify-center py-12 print:hidden">
      <UProgress class="w-12" />
    </div>

    <UAlert v-else-if="loadError" color="error" variant="outline" :description="loadError" class="print:hidden" />

    <template v-else>
      <div class="flex flex-col gap-1">
        <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0 print:text-black">
          Planning checklist
        </h1>
        <p class="text-surface-500 dark:text-surface-400 print:text-black">
          {{ study?.title || `Study #${study?.id}` }}
        </p>
      </div>

      <div v-for="section in sections" :key="section.title" class="flex flex-col gap-2">
        <h2 class="text-lg font-semibold text-surface-900 dark:text-surface-0 print:text-black">
          {{ section.title }}
        </h2>
        <ul class="flex flex-col gap-3">
          <li
            v-for="item in section.items"
            :key="item"
            class="flex items-start gap-3 text-sm text-surface-700 dark:text-surface-200 print:text-black"
          >
            <span
              class="mt-0.5 size-4 shrink-0 rounded-sm border-2 border-surface-400 dark:border-surface-500 print:border-black"
            />
            <span class="flex-1">
              {{ item }}
              <span class="block mt-1 border-b border-dashed border-surface-300 dark:border-surface-600 print:border-black w-full h-5" />
            </span>
          </li>
        </ul>
      </div>

      <div class="flex flex-col gap-2">
        <h2 class="text-lg font-semibold text-surface-900 dark:text-surface-0 print:text-black">
          Notes
        </h2>
        <div
          v-for="n in 4"
          :key="n"
          class="border-b border-dashed border-surface-300 dark:border-surface-600 print:border-black h-7"
        />
      </div>
    </template>
  </div>
</template>
