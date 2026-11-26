export type ReviewStatus = 'draft' | 'in_review' | 'changes_requested' | 'passed'
export type ReviewCommentStatus = 'open' | 'addressed' | 'resolved'

export interface ReviewUser {
  id: string
  first_name: string
  last_name: string
}

export interface ReviewSection {
  key: string
  label: string
}

export interface ReviewRecord {
  id: string
  label: string
}

export interface ReviewRound {
  number: number
  submitted_at: string
  submitted_by: ReviewUser | null
  decision: 'changes_requested' | 'passed' | null
  decided_at: string | null
  decided_by: ReviewUser | null
}

export interface ReviewReply {
  id: string
  body: string
  author: ReviewUser | null
  created_at: string
  edited_at: string | null
}

export interface ReviewComment extends ReviewReply {
  round_number: number | null
  /** "general" or a section key, see StudyReview.sections. */
  section: string
  target_id: string | null
  target_label: string | null
  field_label: string | null
  status: ReviewCommentStatus
  status_changed_at: string | null
  status_changed_by: ReviewUser | null
  replies: ReviewReply[]
}

export interface ReviewProgress {
  total: number
  open: number
  addressed: number
  resolved: number
}

export interface StudyReview {
  study_id: string
  status: ReviewStatus
  rounds: ReviewRound[]
  comments: ReviewComment[]
  progress: ReviewProgress
  sections: ReviewSection[]
  /** The current user reviews as a quality checker: comments, resolves, decides. */
  can_review: boolean
  /** The current user works on the study: replies, marks addressed, submits. */
  can_respond: boolean
}

export interface ReviewQueueEntry {
  study_id: string
  title: string | null
  laboratory_name: string | null
  year: string | null
  status: ReviewStatus
  round_number: number
  submitted_at: string | null
  progress: ReviewProgress
}

export interface ReviewCommentCreate {
  body: string
  section: string
  target_id?: string | null
  target_label?: string | null
  field_label?: string | null
}

export interface ReviewCommentUpdate {
  body?: string
  status?: ReviewCommentStatus
}

export interface ReviewDiffField {
  key: string
  label: string
  old: unknown
  new: unknown
}

export interface ReviewDiffRow {
  id: string
  label: string
  change: 'added' | 'removed' | 'changed'
  fields: ReviewDiffField[]
}

export interface ReviewDiffSection {
  key: string
  label: string
  added: number
  removed: number
  changed: number
  rows: ReviewDiffRow[]
}

export interface StudyReviewDiff {
  from_round: number
  /** null: compared with the study's current data. */
  to_round: number | null
  sections: ReviewDiffSection[]
}
