export type LegalPageMode = 'text' | 'url'

export interface SiteSettings {
  id: number
  site_print_mode: LegalPageMode
  site_print_text?: string | null
  site_print_url?: string | null
  privacy_policy_mode: LegalPageMode
  privacy_policy_text?: string | null
  privacy_policy_url?: string | null
}

export interface SiteSettingsInput {
  site_print_mode?: LegalPageMode
  site_print_text?: string | null
  site_print_url?: string | null
  privacy_policy_mode?: LegalPageMode
  privacy_policy_text?: string | null
  privacy_policy_url?: string | null
}
