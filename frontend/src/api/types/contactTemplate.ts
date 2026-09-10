import type { NamedCategory } from './categories'
import type { ConditionDuringContact } from './contact'
import type { SurfaceTemplate } from './surfaceTemplate'

export interface ContactTemplate {
  id: string
  donor_surface_template_id?: string | null
  donor_surface_template?: SurfaceTemplate | null
  recipient_surface_template_id?: string | null
  recipient_surface_template?: SurfaceTemplate | null
  // Seconds, matching the backend's timedelta field.
  duration?: number | null
  pressure_estimate_id?: string | null
  pressure_estimate?: NamedCategory | null
  friction_applied_estimate_id?: string | null
  friction_applied_estimate?: NamedCategory | null
  contact_area?: number | null
  description_of_contact?: string | null
  activity_category_id?: string | null
  activity_category?: NamedCategory | null
  condition_during_contact_id?: string | null
  condition_during_contact?: ConditionDuringContact | null
}

export interface ContactTemplateInput {
  donor_surface_template_id?: string | null
  recipient_surface_template_id?: string | null
  duration?: number | null
  pressure_estimate_id?: string | null
  friction_applied_estimate_id?: string | null
  contact_area?: number | null
  description_of_contact?: string | null
  activity_category_id?: string | null
  condition_during_contact_id?: string | null
  scenario_ids?: string[]
}
