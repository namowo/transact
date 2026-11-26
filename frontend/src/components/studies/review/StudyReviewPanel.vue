<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { TabsItem } from '@nuxt/ui'
import { useToast } from '@nuxt/ui/composables'
import { getStudyReview, requestChanges, submitForReview } from '@/api/studyReview'
import { passQualityCheck } from '@/api/studies'
import { getErrorMessage } from '@/api/errors'
import type { ReviewCommentStatus, StudyReview } from '@/api/types'
import { useConfirm } from '@/composables/useConfirm'
import ReviewCommentForm, { type CommentDraft } from './ReviewCommentForm.vue'
import ReviewCommentThread from './ReviewCommentThread.vue'
import ReviewDiff from './ReviewDiff.vue'
import { reviewStatusLabels } from './reviewLabels'

// The quality review of a study, beside the study page. The laboratory
// submits the study; quality checkers comment on it (on the study, a section
// or a single record), compare what changed between review rounds, and send
// it back for changes or pass it. Comments track the demanded changes:
// open -> addressed (by the laboratory) -> resolved (by a quality checker).

const props = defineProps<{ studyId: string; studyTitle?: string | null }>()
const open = defineModel<boolean>('open', { default: false })
const emit = defineEmits<{ changed: [review: StudyReview] }>()

const toast = useToast()
const confirm = useConfirm()

const review = ref<StudyReview | null>(null)
const loading = ref(false)
const loadError = ref('')
const acting = ref<'submit' | 'request' | 'pass' | null>(null)

function setReview(value: StudyReview) {
  review.value = value
  emit('changed', value)
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    setReview(await getStudyReview(props.studyId))
  } catch (err) {
    loadError.value = getErrorMessage(err, 'Could not load the review.')
  } finally {
    loading.value = false
  }
}

watch(
  open,
  (isOpen) => {
    if (isOpen) load()
  },
  { immediate: true },
)

function onCommentChanged(value: StudyReview | null) {
  if (value) setReview(value)
  else load()
}

const status = computed(() => (review.value ? reviewStatusLabels[review.value.status] : null))
const currentRound = computed(() => review.value?.rounds.at(-1) ?? null)
const progress = computed(() => review.value?.progress ?? { total: 0, open: 0, addressed: 0, resolved: 0 })
const unresolved = computed(() => progress.value.open + progress.value.addressed)

// --- Workflow ---

async function act(kind: 'submit' | 'request' | 'pass', action: () => Promise<unknown>, done: string) {
  acting.value = kind
  try {
    await action()
    toast.add({ title: done, color: 'success' })
    await load()
  } catch (err) {
    toast.add({ title: getErrorMessage(err, 'That did not work. Please try again.'), color: 'error' })
  } finally {
    acting.value = null
  }
}

function submit() {
  const resubmit = review.value?.status === 'changes_requested'
  const pending = progress.value.open
  confirm.require({
    header: resubmit ? 'Resubmit for quality check' : 'Submit for quality check',
    message: resubmit
      ? pending
        ? `${pending} comment${pending === 1 ? ' is' : 's are'} not marked as addressed yet. Resubmit anyway? Quality checkers will see what you changed since the last round.`
        : 'Resubmit the study? Quality checkers will see what you changed since the last round.'
      : 'Submit the study for quality check? Quality checkers will review it and may ask for changes.',
    acceptLabel: resubmit ? 'Resubmit' : 'Submit',
    rejectLabel: 'Cancel',
    accept: () =>
      act('submit', () => submitForReview(props.studyId), resubmit ? 'Study resubmitted.' : 'Study submitted for quality check.'),
  })
}

function sendBack() {
  confirm.require({
    header: 'Request changes',
    message: progress.value.open
      ? `Send the study back to its laboratory to address ${progress.value.open} open comment${progress.value.open === 1 ? '' : 's'}?`
      : 'Send the study back to its laboratory? There are no open comments - add some first so the laboratory knows what to change.',
    acceptLabel: 'Request changes',
    rejectLabel: 'Cancel',
    acceptColor: 'warning',
    accept: () => act('request', () => requestChanges(props.studyId), 'Changes requested.'),
  })
}

function pass() {
  confirm.require({
    header: 'Pass quality check',
    message: 'Pass the quality check for this study? This also publishes it immediately.',
    acceptLabel: 'Pass & publish',
    rejectLabel: 'Cancel',
    acceptColor: 'success',
    accept: () => act('pass', () => passQualityCheck(props.studyId), 'Quality check passed.'),
  })
}

// --- Comments ---

type Filter = 'unresolved' | ReviewCommentStatus | 'all'
const filter = ref<Filter>('unresolved')
const sectionFilter = ref<string>('all')

const filterItems = computed(() => [
  { label: `Unresolved (${unresolved.value})`, value: 'unresolved' },
  { label: `Open (${progress.value.open})`, value: 'open' },
  { label: `Addressed (${progress.value.addressed})`, value: 'addressed' },
  { label: `Resolved (${progress.value.resolved})`, value: 'resolved' },
  { label: `All (${progress.value.total})`, value: 'all' },
])

const sectionItems = computed(() => [
  { label: 'All sections', value: 'all' },
  ...(review.value?.sections ?? []).map((s) => ({ label: s.label, value: s.key })),
])

// Grouped by section, in the order of the study page.
const groups = computed(() => {
  if (!review.value) return []
  const comments = review.value.comments.filter(
    (c) =>
      (filter.value === 'all' ||
        (filter.value === 'unresolved' ? c.status !== 'resolved' : c.status === filter.value)) &&
      (sectionFilter.value === 'all' || c.section === sectionFilter.value),
  )
  return review.value.sections
    .map((s) => ({ ...s, comments: comments.filter((c) => c.section === s.key) }))
    .filter((g) => g.comments.length)
})

function emptyDraft(): CommentDraft {
  return { section: 'general', target_id: null, target_label: null, field_label: null, body: '' }
}
const composing = ref(false)
const draft = ref<CommentDraft>(emptyDraft())

function onCommentCreated(value: StudyReview) {
  setReview(value)
  composing.value = false
  draft.value = emptyDraft()
  filter.value = 'unresolved'
}

// --- Tabs ---

const tab = ref<'comments' | 'changes'>('comments')
const tabItems = computed<TabsItem[]>(() => [
  { label: 'Comments', value: 'comments', icon: 'i-lucide-messages-square', badge: unresolved.value || undefined },
  { label: 'Changes', value: 'changes', icon: 'i-lucide-git-compare' },
])

function commentOn(target: { section: string; target_id: string; target_label: string; field_label: string | null }) {
  draft.value = { ...emptyDraft(), ...target }
  composing.value = true
  tab.value = 'comments'
}
</script>

<template>
  <USlideover
    v-model:open="open"
    title="Quality review"
    :description="studyTitle || undefined"
    :ui="{ content: 'max-w-2xl w-full', body: 'flex flex-col gap-4' }"
  >
    <template #body>
      <div v-if="loading && !review" class="flex flex-col gap-3" aria-busy="true">
        <USkeleton class="h-16 w-full" />
        <USkeleton v-for="n in 3" :key="n" class="h-24 w-full" />
      </div>

      <UAlert v-else-if="loadError" color="error" variant="outline" :description="loadError" />

      <template v-else-if="review && status">
        <!-- Where the review stands, and what the current user can do next. -->
        <div class="flex flex-wrap items-center gap-2">
          <UBadge :label="status.label" :color="status.color" :icon="status.icon" variant="subtle" />
          <span v-if="currentRound" class="text-sm text-muted">Round {{ currentRound.number }}</span>
        </div>

        <UAlert
          v-if="review.status === 'draft' && review.can_respond"
          color="neutral"
          variant="subtle"
          icon="i-lucide-send"
          title="Not submitted yet"
          description="Submit the study once its data is complete. Quality checkers then review it and may ask for changes."
          :actions="[{ label: 'Submit for quality check', icon: 'i-lucide-send', loading: acting === 'submit', onClick: submit }]"
        />
        <UAlert
          v-else-if="review.status === 'changes_requested' && review.can_respond"
          color="warning"
          variant="subtle"
          icon="i-lucide-message-square-warning"
          title="Changes requested"
          description="Work through the comments, mark each one as addressed, then resubmit the study."
          :actions="[{ label: 'Resubmit', icon: 'i-lucide-send', loading: acting === 'submit', onClick: submit }]"
        />
        <UAlert
          v-else-if="review.status === 'in_review' && review.can_respond && !review.can_review"
          color="info"
          variant="subtle"
          icon="i-lucide-search-check"
          title="In review"
          description="A quality checker is reviewing the study. You can still reply to comments."
        />
        <UAlert
          v-else-if="review.status === 'changes_requested' && review.can_review"
          color="warning"
          variant="subtle"
          icon="i-lucide-hourglass"
          title="Waiting for the laboratory"
          description="The laboratory is working on the requested changes and will resubmit the study."
        />
        <UAlert
          v-else-if="review.status === 'passed'"
          color="success"
          variant="subtle"
          icon="i-lucide-badge-check"
          title="Quality check passed"
          description="The study is published."
        />

        <div v-if="review.status === 'in_review' && review.can_review" class="flex flex-wrap gap-2">
          <UButton
            label="Request changes"
            icon="i-lucide-undo-2"
            color="warning"
            variant="soft"
            :loading="acting === 'request'"
            @click="sendBack"
          />
          <UTooltip
            :text="unresolved ? `Resolve all comments first (${unresolved} unresolved).` : 'Pass and publish the study.'"
          >
            <UButton
              label="Pass quality check"
              icon="i-lucide-badge-check"
              color="success"
              :disabled="unresolved > 0"
              :loading="acting === 'pass'"
              @click="pass"
            />
          </UTooltip>
        </div>

        <!-- Progress on the demanded changes. -->
        <div v-if="progress.total" class="flex flex-col gap-1.5">
          <div class="flex items-center justify-between text-sm">
            <span class="font-medium">{{ progress.resolved }} of {{ progress.total }} resolved</span>
            <span class="text-muted">{{ progress.open }} open · {{ progress.addressed }} addressed</span>
          </div>
          <UProgress :model-value="progress.resolved" :max="progress.total" color="success" size="sm" />
        </div>

        <UTabs v-model="tab" :items="tabItems" :content="false" class="w-full" />

        <template v-if="tab === 'comments'">
          <ReviewCommentForm
            v-if="composing"
            v-model="draft"
            :study-id="studyId"
            :sections="review.sections"
            @created="onCommentCreated"
            @cancel="composing = false"
          />
          <div v-else class="flex flex-wrap items-center gap-2">
            <UButton
              v-if="review.can_review"
              label="New comment"
              icon="i-lucide-message-square-plus"
              size="sm"
              @click="composing = true"
            />
            <USelect v-model="filter" :items="filterItems" size="sm" class="w-44 ml-auto" />
            <USelect v-model="sectionFilter" :items="sectionItems" size="sm" class="w-44" />
          </div>

          <p v-if="!review.comments.length" class="text-sm text-muted py-6 text-center">
            No comments yet.
            <template v-if="review.can_review">Add comments for anything the laboratory should change.</template>
          </p>
          <p v-else-if="!groups.length" class="text-sm text-muted py-6 text-center">No comments match the filter.</p>

          <section v-for="group in groups" :key="group.key" class="flex flex-col gap-2">
            <h3 class="text-sm font-semibold">{{ group.label }}</h3>
            <ReviewCommentThread
              v-for="comment in group.comments"
              :key="comment.id"
              :study-id="studyId"
              :comment="comment"
              :can-review="review.can_review"
              :can-respond="review.can_respond"
              @changed="onCommentChanged"
            />
          </section>
        </template>

        <ReviewDiff
          v-else
          :study-id="studyId"
          :rounds="review.rounds"
          :can-comment="review.can_review"
          @comment="commentOn"
        />
      </template>
    </template>
  </USlideover>
</template>
