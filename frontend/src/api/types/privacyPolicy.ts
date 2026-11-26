import type { LegalPageMode } from './siteSettings'

export type PrivacyPolicyStatus = 'draft' | 'active' | 'archived'

// One version of the privacy policy. Drafts (`version` null) can be edited;
// published versions are frozen.
export interface PrivacyPolicy {
  id: number
  // 1, 2, 3, ... in publishing order; null while a draft.
  version: number | null
  mode: LegalPageMode
  text?: string | null
  url?: string | null
  published_at: string | null
}

export interface PrivacyPolicyAdmin extends PrivacyPolicy {
  status: PrivacyPolicyStatus
  created_at: string
  updated_at: string
  created_by: { first_name: string; last_name: string } | null
  published_by: { first_name: string; last_name: string } | null
  // How many users agreed to this version.
  consent_count: number
}

export interface PrivacyPolicyDraftInput {
  mode?: LegalPageMode
  text?: string | null
  url?: string | null
}
