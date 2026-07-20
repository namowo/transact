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
