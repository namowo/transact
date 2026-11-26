import type { ReviewCommentStatus, ReviewStatus, ReviewUser } from '@/api/types'

type Color = 'primary' | 'secondary' | 'success' | 'info' | 'warning' | 'error' | 'neutral'

export const reviewStatusLabels: Record<ReviewStatus, { label: string; color: Color; icon: string }> = {
  draft: { label: 'Not submitted', color: 'neutral', icon: 'i-lucide-pencil-line' },
  in_review: { label: 'In review', color: 'info', icon: 'i-lucide-search-check' },
  changes_requested: { label: 'Changes requested', color: 'warning', icon: 'i-lucide-message-square-warning' },
  passed: { label: 'Passed', color: 'success', icon: 'i-lucide-badge-check' },
}

export const commentStatusLabels: Record<ReviewCommentStatus, { label: string; color: Color; icon: string }> = {
  open: { label: 'Open', color: 'warning', icon: 'i-lucide-circle-dot' },
  addressed: { label: 'Addressed', color: 'info', icon: 'i-lucide-circle-check' },
  resolved: { label: 'Resolved', color: 'success', icon: 'i-lucide-check-check' },
}

export function userName(user: ReviewUser | null | undefined): string {
  return user ? `${user.first_name} ${user.last_name}`.trim() : 'Deleted user'
}

export function formatDateTime(value: string | null | undefined): string {
  return value ? new Date(value).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : '—'
}

/** A snapshot value as shown in the change view. */
export function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  return String(value)
}

export function reviewStatusOf(status: ReviewStatus | null | undefined) {
  return reviewStatusLabels[status ?? 'draft']
}
