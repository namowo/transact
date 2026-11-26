import type { Laboratory } from './laboratory'
import type { Permission, UserGroupBrief } from './userGroup'

// Data tables whose column sort is saved on the user.
export type SortableTable = 'samples' | 'results'

export interface TableSortMeta {
  field: string
  order: 1 | -1
}

export type NotificationChannel = 'email' | 'browser'
export type NotificationTypeKey =
  'lab_membership_request' | 'laboratory_request' | 'study_quality_checked'
export type NotificationSettings = Partial<
  Record<NotificationTypeKey, Partial<Record<NotificationChannel, boolean>>>
>

// A notification the user's permissions let them receive.
export interface NotificationTypeInfo {
  key: NotificationTypeKey
  label: string
  description: string
  channels: NotificationChannel[]
}

export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  is_active: boolean
  is_verified: boolean
  // Locked after too many wrong passwords; an admin has to unlock it.
  is_locked: boolean
  // Invited, but hasn't accepted the invitation (chosen a password) yet.
  invitation_pending: boolean
  groups: UserGroupBrief[]
  // Everything the user's groups grant. Laboratory permissions only apply
  // to the user's own laboratory.
  permissions: Permission[]
  passkey_prompt_dismissed: boolean
  // Authenticator app (one-time codes) set up as a second factor.
  totp_enabled: boolean
  // Unused recovery codes for the authenticator app.
  recovery_codes_remaining: number
  // Signed in, but two-factor authentication is required and the user has
  // no second factor yet: they may only set one up.
  two_factor_setup_required: boolean
  // Interactive guides the user finished or skipped.
  completed_tours?: string[]
  // Privacy policy versions the user agreed to.
  accepted_privacy_policy_ids: number[]
  locale: string
  // Per notification type and channel, defaults filled in.
  notification_settings: NotificationSettings
  table_sorts?: Partial<Record<SortableTable, TableSortMeta[]>> | null
  laboratory_id: string | null
  laboratory?: Laboratory | null
  created_at: string
}

export interface RegisterPayload {
  email: string
  password: string
  first_name: string
  last_name: string
  // The privacy policy version the user agreed to, if one is published.
  privacy_policy_id?: number | null
}

// The instance's sign-up and sign-in policy (set in the backend environment).
export interface AuthConfig {
  registration_enabled: boolean
  invitations_enabled: boolean
  two_factor_required: boolean
}

// The password was right, but a second factor is needed. With 'totp', send
// a code with `login_token`; with 'passkey', sign in with a passkey instead.
export interface TwoFactorChallenge {
  two_factor_required: true
  login_token: string | null
  methods: ('totp' | 'passkey')[]
}

export interface TotpSetup {
  secret: string
  // otpauth:// link, shown as a QR code.
  provisioning_uri: string
}

export interface RecoveryCodes {
  recovery_codes: string[]
}

export interface SetupStatus {
  needs_setup: boolean
}

export interface SuperuserSetupPayload {
  email: string
  password: string
  first_name: string
  last_name: string
}

export interface WebAuthnCredential {
  id: string
  device_name: string | null
  created_at: string
  last_used_at: string | null
}

export interface ApiKey {
  id: string
  name: string | null
  prefix: string
  created_at: string
  last_used_at: string | null
  expires_at: string | null
}

export interface ApiKeyCreated extends ApiKey {
  token: string
}

export interface ApiKeyCreatePayload {
  name?: string
  expires_at?: string
}
