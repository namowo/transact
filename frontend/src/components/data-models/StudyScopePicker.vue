<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { listDownloadableStudies } from '@/api/dataModels'
import type { DownloadableStudy } from '@/api/types'
import StudyPickerModal from '@/components/data-models/StudyPickerModal.vue'
import { useAuthStore } from '@/stores/auth'

const studyIds = defineModel<string[] | null>({ required: true })

const props = withDefaults(defineProps<{ allDescription?: string }>(), {
  allDescription: 'New studies are included automatically on every download.',
})

const auth = useAuthStore()
const studies = ref<DownloadableStudy[]>([])
const loading = ref(false)
const pickerOpen = ref(false)

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
    if (value === 'all') {
      studyIds.value = null
    } else {
      studyIds.value = studyIds.value ?? []
      // Nothing chosen yet: go straight to choosing.
      if (!studyIds.value.length) pickerOpen.value = true
    }
  },
})

const byId = computed(() => new Map(studies.value.map((s) => [s.id, s])))

const selectedStudies = computed(() =>
  (studyIds.value ?? []).map((id) => byId.value.get(id)).filter((s): s is DownloadableStudy => !!s),
)

const SHOWN = 6
const shownStudies = computed(() => selectedStudies.value.slice(0, SHOWN))
const moreCount = computed(() => selectedStudies.value.length - shownStudies.value.length)

function studyLabel(study: DownloadableStudy) {
  return study.year ? `${study.title} (${study.year})` : study.title
}

function removeStudy(id: string) {
  studyIds.value = (studyIds.value ?? []).filter((s) => s !== id)
}

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
      variant="table"
      :items="[
        { label: 'All available studies', value: 'all', description: props.allDescription },
        { label: 'Selected studies only', value: 'some' },
      ]"
    />

    <div v-if="mode === 'some'" class="flex flex-col gap-2">
      <div class="flex flex-wrap items-center gap-2">
        <UButton
          :label="selectedStudies.length ? 'Change selection' : 'Choose studies'"
          icon="i-lucide-list-checks"
          color="neutral"
          variant="outline"
          :loading="loading"
          @click="pickerOpen = true"
        />
        <span class="text-sm text-muted">
          {{ selectedStudies.length }} of {{ studies.length }}
          {{ studies.length === 1 ? 'study' : 'studies' }} selected
        </span>
        <UButton
          v-if="selectedStudies.length"
          label="Clear"
          variant="link"
          color="neutral"
          @click="studyIds = []"
        />
      </div>
      <div v-if="shownStudies.length" class="flex flex-wrap gap-1.5">
        <UBadge
          v-for="study in shownStudies"
          :key="study.id"
          color="neutral"
          variant="subtle"
          class="max-w-full"
        >
          <span class="truncate">{{ studyLabel(study) }}</span>
          <UButton
            icon="i-lucide-x"
            size="xs"
            variant="link"
            color="neutral"
            class="-me-1 p-0"
            :aria-label="`Remove ${study.title}`"
            @click="removeStudy(study.id)"
          />
        </UBadge>
        <UButton
          v-if="moreCount > 0"
          :label="`+${moreCount} more`"
          size="xs"
          variant="ghost"
          color="neutral"
          @click="pickerOpen = true"
        />
      </div>
    </div>

    <StudyPickerModal
      v-model:open="pickerOpen"
      :studies="studies"
      :loading="loading"
      :selected="studyIds ?? []"
      @apply="studyIds = $event"
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
