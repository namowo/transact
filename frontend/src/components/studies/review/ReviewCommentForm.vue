<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useToast } from '@nuxt/ui/composables'
import { createReviewComment, getReviewRecords } from '@/api/studyReview'
import { getErrorMessage } from '@/api/errors'
import type { ReviewRecord, ReviewSection, StudyReview } from '@/api/types'

// A quality checker's new comment: on the study as a whole, a section, or a
// single record of a section (picked here, or pinned from the change view).

export interface CommentDraft {
  section: string
  target_id: string | null
  target_label: string | null
  field_label: string | null
  body: string
}

const props = defineProps<{ studyId: string; sections: ReviewSection[] }>()
const draft = defineModel<CommentDraft>({ required: true })
const emit = defineEmits<{ created: [review: StudyReview]; cancel: [] }>()

const toast = useToast()
const saving = ref(false)
const records = ref<Record<string, ReviewRecord[]> | null>(null)
const loadingRecords = ref(false)

async function loadRecords() {
  if (records.value || loadingRecords.value) return
  loadingRecords.value = true
  try {
    records.value = await getReviewRecords(props.studyId)
  } catch {
    records.value = {}
  } finally {
    loadingRecords.value = false
  }
}

watch(
  () => draft.value.section,
  (section) => {
    if (section !== 'general') loadRecords()
  },
  { immediate: true },
)

const sectionItems = computed(() => props.sections.map((s) => ({ label: s.label, value: s.key })))

const recordItems = computed(() => {
  const list = records.value?.[draft.value.section] ?? []
  const items = list.map((r) => ({ label: r.label, value: r.id }))
  // A record pinned from the change view may be gone from the current data
  // (e.g. removed) - keep it selectable.
  if (draft.value.target_id && !items.some((i) => i.value === draft.value.target_id)) {
    items.unshift({ label: draft.value.target_label ?? draft.value.target_id, value: draft.value.target_id })
  }
  return items
})

const targetId = computed({
  get: () => draft.value.target_id ?? undefined,
  set: (value: string | undefined | null) => {
    const item = recordItems.value.find((i) => i.value === value)
    draft.value = {
      ...draft.value,
      target_id: value ?? null,
      target_label: item?.label ?? null,
      field_label: null,
    }
  },
})

function onSectionChange(section: string) {
  draft.value = { ...draft.value, section, target_id: null, target_label: null, field_label: null }
}

async function submit() {
  if (!draft.value.body.trim()) return
  saving.value = true
  try {
    const review = await createReviewComment(props.studyId, {
      body: draft.value.body,
      section: draft.value.section,
      target_id: draft.value.target_id,
      target_label: draft.value.target_label,
      field_label: draft.value.field_label,
    })
    emit('created', review)
  } catch (err) {
    toast.add({ title: getErrorMessage(err, 'Could not add the comment.'), color: 'error' })
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <form class="flex flex-col gap-3 rounded-lg border border-default p-3" @submit.prevent="submit">
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <UFormField label="About">
        <USelect
          :model-value="draft.section"
          :items="sectionItems"
          class="w-full"
          @update:model-value="onSectionChange($event as string)"
        />
      </UFormField>
      <UFormField v-if="draft.section !== 'general'" label="Record" hint="Optional">
        <USelectMenu
          v-model="targetId"
          :items="recordItems"
          value-key="value"
          :loading="loadingRecords"
          placeholder="The whole section"
          clear
          class="w-full"
        />
      </UFormField>
    </div>
    <p v-if="draft.field_label" class="text-xs text-muted flex items-center gap-1">
      Field: <span class="font-medium">{{ draft.field_label }}</span>
      <UButton
        icon="i-lucide-x"
        color="neutral"
        variant="link"
        size="xs"
        aria-label="Remove field"
        @click="draft = { ...draft, field_label: null }"
      />
    </p>
    <UFormField label="Comment">
      <UTextarea
        v-model="draft.body"
        :rows="3"
        autoresize
        autofocus
        placeholder="What needs to change?"
        class="w-full"
      />
    </UFormField>
    <div class="flex justify-end gap-2">
      <UButton label="Cancel" color="neutral" variant="ghost" size="sm" @click="emit('cancel')" />
      <UButton type="submit" label="Add comment" icon="i-lucide-message-square-plus" size="sm" :loading="saving" :disabled="!draft.body.trim()" />
    </div>
  </form>
</template>
