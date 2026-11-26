<script setup lang="ts">
import { computed, ref } from 'vue'
import type { DropdownMenuItem } from '@nuxt/ui'
import { useToast } from '@nuxt/ui/composables'
import {
  deleteReviewComment,
  replyToReviewComment,
  updateReviewComment,
} from '@/api/studyReview'
import { getErrorMessage } from '@/api/errors'
import type { ReviewComment, ReviewCommentStatus, StudyReview } from '@/api/types'
import { useConfirm } from '@/composables/useConfirm'
import { useAuthStore } from '@/stores/auth'
import { commentStatusLabels, formatDateTime, userName } from './reviewLabels'

// One review comment with its replies. Quality checkers resolve or reopen it,
// the study's laboratory marks it addressed; both can reply.

const props = defineProps<{
  studyId: string
  comment: ReviewComment
  canReview: boolean
  canRespond: boolean
}>()

const emit = defineEmits<{ changed: [review: StudyReview | null] }>()

const auth = useAuthStore()
const toast = useToast()
const confirm = useConfirm()

const busy = ref(false)
const replying = ref(false)
const replyBody = ref('')
const editing = ref(false)
const editBody = ref('')

const status = computed(() => commentStatusLabels[props.comment.status])
const isAuthor = computed(() => !!auth.user && props.comment.author?.id === auth.user.id)
const canReply = computed(() => props.canReview || props.canRespond)

async function run(action: () => Promise<StudyReview | void>, failure: string) {
  busy.value = true
  try {
    const review = await action()
    emit('changed', review ?? null)
    return true
  } catch (err) {
    toast.add({ title: getErrorMessage(err, failure), color: 'error' })
    return false
  } finally {
    busy.value = false
  }
}

function setStatus(value: ReviewCommentStatus) {
  run(
    () => updateReviewComment(props.studyId, props.comment.id, { status: value }),
    'Could not change the comment.',
  )
}

async function sendReply() {
  if (!replyBody.value.trim()) return
  const ok = await run(
    () => replyToReviewComment(props.studyId, props.comment.id, replyBody.value),
    'Could not send the reply.',
  )
  if (ok) {
    replyBody.value = ''
    replying.value = false
  }
}

function startEditing() {
  editBody.value = props.comment.body
  editing.value = true
}

async function saveEdit() {
  if (!editBody.value.trim()) return
  const ok = await run(
    () => updateReviewComment(props.studyId, props.comment.id, { body: editBody.value }),
    'Could not save the comment.',
  )
  if (ok) editing.value = false
}

function remove(id: string, isReply: boolean) {
  confirm.require({
    header: isReply ? 'Delete reply' : 'Delete comment',
    message: isReply
      ? 'Delete this reply?'
      : 'Delete this comment and all replies? It no longer counts towards the review progress.',
    acceptLabel: 'Delete',
    rejectLabel: 'Cancel',
    acceptColor: 'error',
    accept: () => run(() => deleteReviewComment(props.studyId, id), 'Could not delete.'),
  })
}

const menuItems = computed<DropdownMenuItem[]>(() => [
  { label: 'Edit', icon: 'i-lucide-pencil', onSelect: startEditing },
  {
    label: 'Delete',
    icon: 'i-lucide-trash-2',
    color: 'error',
    onSelect: () => remove(props.comment.id, false),
  },
])

const statusHint = computed(() => {
  const c = props.comment
  if (!c.status_changed_at || c.status === 'open') return ''
  return `${status.value.label} by ${userName(c.status_changed_by)}, ${formatDateTime(c.status_changed_at)}`
})
</script>

<template>
  <div
    class="rounded-lg border border-default p-3 flex flex-col gap-2"
    :class="{ 'opacity-70': comment.status === 'resolved' }"
  >
    <div class="flex flex-wrap items-center gap-2">
      <UBadge :label="status.label" :color="status.color" :icon="status.icon" variant="subtle" size="sm" />
      <span v-if="comment.target_label" class="text-sm font-medium truncate">
        <UIcon name="i-lucide-crosshair" class="size-3.5 align-middle text-muted" />
        {{ comment.target_label }}<template v-if="comment.field_label"> · {{ comment.field_label }}</template>
      </span>
      <UDropdownMenu v-if="isAuthor" :items="menuItems" class="ml-auto">
        <UButton icon="i-lucide-ellipsis" color="neutral" variant="ghost" size="xs" aria-label="Comment actions" />
      </UDropdownMenu>
    </div>

    <div v-if="editing" class="flex flex-col gap-2">
      <UTextarea v-model="editBody" :rows="3" autoresize class="w-full" />
      <div class="flex gap-2 justify-end">
        <UButton label="Cancel" color="neutral" variant="ghost" size="sm" @click="editing = false" />
        <UButton label="Save" size="sm" :loading="busy" :disabled="!editBody.trim()" @click="saveEdit" />
      </div>
    </div>
    <p v-else class="text-sm whitespace-pre-wrap">{{ comment.body }}</p>

    <p class="text-xs text-muted">
      {{ userName(comment.author) }} · {{ formatDateTime(comment.created_at) }}
      <template v-if="comment.round_number"> · Round {{ comment.round_number }}</template>
      <template v-if="comment.edited_at"> · edited</template>
    </p>
    <p v-if="statusHint" class="text-xs text-muted">{{ statusHint }}</p>

    <div v-if="comment.replies.length" class="flex flex-col gap-2 border-l-2 border-default pl-3 ml-1">
      <div v-for="reply in comment.replies" :key="reply.id" class="flex flex-col gap-0.5">
        <p class="text-sm whitespace-pre-wrap">{{ reply.body }}</p>
        <p class="text-xs text-muted flex items-center gap-1">
          {{ userName(reply.author) }} · {{ formatDateTime(reply.created_at) }}
          <UButton
            v-if="auth.user && reply.author?.id === auth.user.id"
            icon="i-lucide-trash-2"
            color="neutral"
            variant="link"
            size="xs"
            aria-label="Delete reply"
            @click="remove(reply.id, true)"
          />
        </p>
      </div>
    </div>

    <div v-if="replying" class="flex flex-col gap-2">
      <UTextarea v-model="replyBody" placeholder="Write a reply…" :rows="2" autoresize autofocus class="w-full" />
      <div class="flex gap-2 justify-end">
        <UButton label="Cancel" color="neutral" variant="ghost" size="sm" @click="replying = false" />
        <UButton label="Reply" size="sm" :loading="busy" :disabled="!replyBody.trim()" @click="sendReply" />
      </div>
    </div>

    <div v-if="!replying" class="flex flex-wrap gap-1">
      <UButton
        v-if="canReply"
        label="Reply"
        icon="i-lucide-reply"
        color="neutral"
        variant="ghost"
        size="xs"
        @click="replying = true"
      />
      <UButton
        v-if="canRespond && comment.status === 'open'"
        label="Mark as addressed"
        icon="i-lucide-circle-check"
        color="info"
        variant="soft"
        size="xs"
        :loading="busy"
        @click="setStatus('addressed')"
      />
      <UButton
        v-if="canRespond && !canReview && comment.status === 'addressed'"
        label="Not addressed yet"
        icon="i-lucide-undo-2"
        color="neutral"
        variant="ghost"
        size="xs"
        :loading="busy"
        @click="setStatus('open')"
      />
      <UButton
        v-if="canReview && comment.status !== 'resolved'"
        label="Resolve"
        icon="i-lucide-check-check"
        color="success"
        variant="soft"
        size="xs"
        :loading="busy"
        @click="setStatus('resolved')"
      />
      <UButton
        v-if="canReview && comment.status !== 'open'"
        label="Reopen"
        icon="i-lucide-rotate-ccw"
        color="warning"
        variant="ghost"
        size="xs"
        :loading="busy"
        @click="setStatus('open')"
      />
    </div>
  </div>
</template>
