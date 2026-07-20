import type { NamedCategory } from './categories'
import type { Contact } from './contact'
import type { Persistence } from './persistence'

export interface Scenario {
  id: number
  realistic?: boolean | null
  scenario_category_id?: number | null
  scenario_category?: NamedCategory | null
  study_id?: number | null
  persistence_id?: number | null
  persistence?: Persistence | null
  contacts: Contact[]
}

export interface ScenarioInput {
  realistic?: boolean | null
  scenario_category_id?: number | null
  study_id?: number | null
  persistence_id?: number | null
}
