export interface Laboratory {
  id: number
  laboratory_name: string
  country?: string | null
  postal_code?: string | null
  state?: string | null
  city?: string | null
  street_address?: string | null
  institutional_affiliation?: string | null
  director_head_of_laboratory?: string | null
  email?: string | null
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

export interface Token {
  access_token: string
  token_type: string
}
