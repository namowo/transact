import type { NamedCategory } from './categories'
import type { Surface } from './surface'

export interface ConditionDuringContact {
  id: number
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

export interface ConditionDuringContactInput {
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

export interface Contact {
  id: number
  scenario_id?: number | null
  donor_surface_id?: number | null
  donor_surface?: Surface | null
  recipient_surface_id?: number | null
  recipient_surface?: Surface | null
  // Seconds, matching the backend's timedelta field.
  duration?: number | null
  pressure?: number | null
  friction_applied?: number | null
  contact_area?: number | null
  description_of_contact?: string | null
  activity_category_id?: number | null
  activity_category?: NamedCategory | null
  condition_during_contact_id?: number | null
  condition_during_contact?: ConditionDuringContact | null
}

export interface ContactInput {
  scenario_id?: number | null
  donor_surface_id?: number | null
  recipient_surface_id?: number | null
  // Seconds, matching the backend's timedelta field.
  duration?: number | null
  pressure?: number | null
  friction_applied?: number | null
  contact_area?: number | null
  description_of_contact?: string | null
  activity_category_id?: number | null
  condition_during_contact_id?: number | null
}
