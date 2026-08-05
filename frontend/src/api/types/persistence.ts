import type { NamedCategory } from './categories'
import type { Study } from './study'

export interface Persistence {
  id: number
  // The study this persistence was created for - only that study may edit
  // it; other studies may only link it read-only.
  owning_study_id?: number | null
  owning_study?: Study | null
  // Optional label to tell apart multiple persistencies on a scenario.
  name?: string | null
  interval_of_persistence?: number | null
  temperature?: number | null
  humidity?: number | null
  uv_irradiation?: number | null
  indoors?: boolean | null
  change_over_time?: boolean | null
  // Seconds, matching the backend's timedelta field.
  duration_of_disturbance?: number | null
  description_of_disturbance?: string | null
  disturbance_category_id?: number | null
  disturbance_category?: NamedCategory | null
  geographic_location_category_id?: number | null
  geographic_location_category?: NamedCategory | null
}

export interface PersistenceInput {
  // Only accepted on create - immutable afterwards.
  owning_study_id?: number | null
  name?: string | null
  interval_of_persistence?: number | null
  temperature?: number | null
  humidity?: number | null
  uv_irradiation?: number | null
  indoors?: boolean | null
  change_over_time?: boolean | null
  // Seconds, matching the backend's timedelta field.
  duration_of_disturbance?: number | null
  description_of_disturbance?: string | null
  disturbance_category_id?: number | null
  geographic_location_category_id?: number | null
}
