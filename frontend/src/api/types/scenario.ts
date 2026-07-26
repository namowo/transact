import type { NamedCategory } from './categories'
import type { ContactTemplate } from './contactTemplate'
import type { Persistence } from './persistence'
import type { Study } from './study'

export interface Scenario {
  id: number
  realistic?: boolean | null
  scenario_category_id?: number | null
  scenario_category?: NamedCategory | null
  studies: Study[]
  contact_templates: ContactTemplate[]
  persistencies: Persistence[]
}

export interface ScenarioInput {
  realistic?: boolean | null
  scenario_category_id?: number | null
  study_ids?: number[]
  contact_template_ids?: number[]
  persistence_ids?: number[]
}
