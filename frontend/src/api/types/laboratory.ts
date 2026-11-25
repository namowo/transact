export type LaboratoryApprovalStatus = 'pending' | 'approved' | 'denied'

export interface Laboratory {
  id: string
  laboratory_name: string
  country?: string | null
  postal_code?: string | null
  state?: string | null
  city?: string | null
  street_address?: string | null
  institutional_affiliation?: string | null
  director_head_of_laboratory?: string | null
  email?: string | null
  approval_status: LaboratoryApprovalStatus
  // Whether platform admins with "Edit data of all laboratories" may work on
  // this laboratory's studies. The laboratory's own admins decide.
  allow_admin_data_entry: boolean
}

export interface LaboratoryCreate {
  laboratory_name: string
  country: string
  postal_code?: string | null
  state?: string | null
  city: string
  street_address?: string | null
  institutional_affiliation: string
  director_head_of_laboratory?: string | null
  email?: string | null
}
