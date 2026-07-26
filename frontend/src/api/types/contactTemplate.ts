import type { NamedCategory } from './categories'
import type { ConditionDuringContact } from './contact'
import type { SurfaceTemplate } from './surfaceTemplate'

export interface ContactTemplate {
  id: number
  donor_surface_template_id?: number | null
  donor_surface_template?: SurfaceTemplate | null
  recipient_surface_template_id?: number | null
  recipient_surface_template?: SurfaceTemplate | null
  // Seconds, matching the backend's timedelta field.
  duration?: number | null
  pressure?: number | null
  pressure_estimate_id?: number | null
  pressure_estimate?: NamedCategory | null
  friction_applied?: number | null
  friction_applied_estimate_id?: number | null
  friction_applied_estimate?: NamedCategory | null
  contact_area?: number | null
  description_of_contact?: string | null
  activity_category_id?: number | null
  activity_category?: NamedCategory | null
  condition_during_contact_id?: number | null
  condition_during_contact?: ConditionDuringContact | null
}

export interface ContactTemplateInput {
  donor_surface_template_id?: number | null
  recipient_surface_template_id?: number | null
  duration?: number | null
  pressure?: number | null
  pressure_estimate_id?: number | null
  friction_applied?: number | null
  friction_applied_estimate_id?: number | null
  contact_area?: number | null
  description_of_contact?: string | null
  activity_category_id?: number | null
  condition_during_contact_id?: number | null
  scenario_ids?: number[]
}
