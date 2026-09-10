import type { User } from './auth'
import type { Laboratory, LaboratoryCreate } from './laboratory'

export type LabMembershipRequestStatus = 'pending' | 'approved' | 'denied'

export interface LabMembershipRequest {
  id: string
  user_id: string
  user: User
  laboratory_id: string
  laboratory: Laboratory
  status: LabMembershipRequestStatus
  reviewed_by_id: string | null
  reviewed_by: User | null
  reviewed_at: string | null
  created_at: string
}

export interface JoinExistingLabPayload {
  laboratory_id: string
}

export type NewLabRequestPayload = LaboratoryCreate
