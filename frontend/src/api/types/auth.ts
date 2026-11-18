import type { Laboratory } from './laboratory'

// Data tables whose column sort is saved on the user.
export type SortableTable = 'samples' | 'results'

export interface TableSortMeta {
  field: string
  order: 1 | -1
}

export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  is_active: boolean
  is_verified: boolean
  is_superuser: boolean
  can_quality_check: boolean
  can_manage_lab_users: boolean
  passkey_prompt_dismissed: boolean
  // Interactive guides the user finished or skipped.
  completed_tours?: string[]
  locale: string
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
