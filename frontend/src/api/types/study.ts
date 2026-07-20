import type { Laboratory } from './laboratory'

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
  published?: boolean | null
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
  published?: boolean | null
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
  published?: boolean | null
  corresponding_author_name?: string | null
  corresponding_author_email?: string | null
  corresponding_author_phone?: string | null
}
