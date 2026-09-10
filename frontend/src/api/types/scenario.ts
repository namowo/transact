import type { NamedCategory } from './categories'
import type { ContactTemplate } from './contactTemplate'
import type { Persistence } from './persistence'
import type { Study } from './study'

export interface Scenario {
  id: string
  realistic?: boolean | null
  scenario_category_id?: string | null
  owning_study_id?: string | null
  scenario_category?: NamedCategory | null
  studies: Study[]
  contact_templates: ContactTemplate[]
  persistencies: Persistence[]
}

export interface ScenarioInput {
  realistic?: boolean | null
  scenario_category_id?: string | null
  owning_study_id?: string | null
  study_ids?: string[]
  contact_template_ids?: string[]
  persistence_ids?: string[]
}
