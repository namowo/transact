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

export interface Author {
  id: number
  title?: string | null
  first_name: string
  last_name: string
}

export interface AuthorInput {
  title?: string | null
  first_name: string
  last_name: string
}

export interface Study {
  id: number
  laboratory_id: number | null
  laboratory?: Laboratory | null
  doi?: string | null
  authors: Author[]
  description?: string | null
  year?: string | null
  title?: string | null
  abstract?: string | null
  journal?: string | null
  plan_a_transfer_experiment?: boolean | null
  add_data_to_repository?: boolean | null
  quality_check_passed?: boolean | null
  corresponding_author_name?: string | null
  corresponding_author_email?: string | null
  corresponding_author_phone?: string | null
}

export interface StudyCreate {
  laboratory_id: number
  title: string
  authors: AuthorInput[]
  doi?: string | null
  description?: string | null
  year?: string | null
  abstract?: string | null
  journal?: string | null
  plan_a_transfer_experiment?: boolean | null
  add_data_to_repository?: boolean | null
  quality_check_passed?: boolean | null
  corresponding_author_name?: string | null
  corresponding_author_email?: string | null
  corresponding_author_phone?: string | null
}

export interface StudyUpdate {
  laboratory_id?: number | null
  doi?: string | null
  authors?: AuthorInput[]
  description?: string | null
  year?: string | null
  title?: string | null
  abstract?: string | null
  journal?: string | null
  plan_a_transfer_experiment?: boolean | null
  add_data_to_repository?: boolean | null
  quality_check_passed?: boolean | null
  corresponding_author_name?: string | null
  corresponding_author_email?: string | null
  corresponding_author_phone?: string | null
}

export interface RegisterPayload {
  email: string
  password: string
  first_name: string
  last_name: string
}
