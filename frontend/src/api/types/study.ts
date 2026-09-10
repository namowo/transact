import type { Laboratory } from './laboratory'
import type { User } from './auth'

export interface Author {
  id: string
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
  id: string
  laboratory_id: string | null
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
  quality_checked_by_id?: string | null
  quality_checked_by?: User | null
  quality_checked_at?: string | null
}

export interface StudyCreate {
  laboratory_id: string
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
  laboratory_id?: string | null
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
