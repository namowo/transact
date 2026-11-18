<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { listDownloadableStudies } from '@/api/dataModels'
import type { DownloadableStudy } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

const studyIds = defineModel<string[] | null>({ required: true })

const auth = useAuthStore()
const studies = ref<DownloadableStudy[]>([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    studies.value = await listDownloadableStudies()
  } finally {
    loading.value = false
  }
})

const mode = computed({
  get: () => (studyIds.value === null ? 'all' : 'some'),
  set: (value: string) => {
    studyIds.value = value === 'all' ? null : (studyIds.value ?? [])
  },
})

const items = computed(() =>
  studies.value.map((study) => ({
    label: study.year ? `${study.title} (${study.year})` : study.title,
    value: study.id,
    description: [study.laboratory_name, study.published ? null : 'unpublished, your laboratory']
      .filter(Boolean)
      .join(' · '),
  })),
)

const unpublishedCount = computed(() => studies.value.filter((s) => !s.published).length)

// Saved models may reference studies the viewer can't (or can no longer)
// see; those are ignored by the server, so only count the visible ones.
const missing = computed(() => {
  const known = new Set(studies.value.map((s) => s.id))
  return (studyIds.value ?? []).filter((id) => !known.has(id)).length
})
</script>

<template>
  <div class="flex flex-col gap-3">
    <URadioGroup
      v-model="mode"
      :items="[
        {
          label: 'All available studies',
          value: 'all',
          description: 'New studies are included automatically on every download.',
        },
        { label: 'Selected studies only', value: 'some' },
      ]"
    />

    <USelectMenu
      v-if="mode === 'some'"
      v-model="studyIds as string[]"
      :items="items"
      value-key="value"
      multiple
      :loading="loading"
      placeholder="Choose studies"
      :search-input="{ placeholder: 'Search studies…' }"
      class="w-full"
    />

    <p class="text-xs text-muted">
      <template v-if="loading">Loading studies…</template>
      <template v-else>
        {{ studies.length }} {{ studies.length === 1 ? 'study' : 'studies' }} available.
        <template v-if="auth.isAuthenticated && unpublishedCount">
          {{ unpublishedCount }} of them {{ unpublishedCount === 1 ? 'is' : 'are' }} your
          laboratory's unpublished work, which only members of your laboratory can download.
        </template>
        <template v-else-if="!auth.isAuthenticated">
          Published, quality-checked studies are available to everyone. Sign in to also include your
          laboratory's own studies.
        </template>
      </template>
    </p>
    <UAlert
      v-if="missing"
      color="warning"
      variant="subtle"
      :description="`${missing} selected ${missing === 1 ? 'study is' : 'studies are'} not available to you and will be skipped.`"
    />
  </div>
</template>
