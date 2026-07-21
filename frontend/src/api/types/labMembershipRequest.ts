import type { User } from './auth'
import type { Laboratory, LaboratoryCreate } from './laboratory'

export type LabMembershipRequestStatus = 'pending' | 'approved' | 'denied'

export interface LabMembershipRequest {
  id: number
  user_id: number
  user: User
  laboratory_id: number
  laboratory: Laboratory
  status: LabMembershipRequestStatus
  reviewed_by_id: number | null
  reviewed_by: User | null
  reviewed_at: string | null
  created_at: string
}

export interface JoinExistingLabPayload {
  laboratory_id: number
}

export type NewLabRequestPayload = LaboratoryCreate
