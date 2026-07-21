import type { Laboratory } from './laboratory'

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  is_active: boolean
  is_verified: boolean
  is_superuser: boolean
  can_quality_check: boolean
  can_manage_lab_users: boolean
  passkey_prompt_dismissed: boolean
  laboratory_id: number | null
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
  id: number
  device_name: string | null
  created_at: string
  last_used_at: string | null
}
