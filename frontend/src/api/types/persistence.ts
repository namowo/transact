import type { NamedCategory } from './categories'

export interface Persistence {
  id: number
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
