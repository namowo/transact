import apiClient from './client'
import type {
  ReviewCommentCreate,
  ReviewCommentUpdate,
  ReviewQueueEntry,
  ReviewRecord,
  StudyReview,
  StudyReviewDiff,
} from './types'

const base = (studyId: string) => `/studies/${studyId}/review`

/** Studies submitted for quality check or sent back for changes (quality checkers). */
export function getReviewQueue() {
  return apiClient.get<ReviewQueueEntry[]>('/studies/review-queue').then((r) => r.data)
}

export function getStudyReview(studyId: string) {
  return apiClient.get<StudyReview>(base(studyId)).then((r) => r.data)
}

/** Submits the study for quality check, or resubmits it after changes. */
export function submitForReview(studyId: string) {
  return apiClient.post<StudyReview>(`${base(studyId)}/submit`).then((r) => r.data)
}

/** Sends the study back to its laboratory (quality checkers). */
export function requestChanges(studyId: string) {
  return apiClient.post<StudyReview>(`${base(studyId)}/request-changes`).then((r) => r.data)
}

/** What changed from one round to another, or to the current data without `toRound`. */
export function getReviewDiff(studyId: string, fromRound: number, toRound?: number | null) {
  return apiClient
    .get<StudyReviewDiff>(`${base(studyId)}/diff`, {
      params: { from_round: fromRound, to_round: toRound ?? undefined },
    })
    .then((r) => r.data)
}

/** The study's records per section, to pin comments to (quality checkers). */
export function getReviewRecords(studyId: string) {
  return apiClient
    .get<{ records: Record<string, ReviewRecord[]> }>(`${base(studyId)}/records`)
    .then((r) => r.data.records)
}

export function createReviewComment(studyId: string, payload: ReviewCommentCreate) {
  return apiClient.post<StudyReview>(`${base(studyId)}/comments`, payload).then((r) => r.data)
}

export function replyToReviewComment(studyId: string, commentId: string, body: string) {
  return apiClient
    .post<StudyReview>(`${base(studyId)}/comments/${commentId}/replies`, { body })
    .then((r) => r.data)
}

export function updateReviewComment(studyId: string, commentId: string, payload: ReviewCommentUpdate) {
  return apiClient
    .patch<StudyReview>(`${base(studyId)}/comments/${commentId}`, payload)
    .then((r) => r.data)
}

export function deleteReviewComment(studyId: string, commentId: string) {
  return apiClient.delete<void>(`${base(studyId)}/comments/${commentId}`).then((r) => r.data)
}
