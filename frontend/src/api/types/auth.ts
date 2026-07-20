import type { Laboratory } from './laboratory'

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  is_active: boolean
  is_verified: boolean
  is_superuser: boolean
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
