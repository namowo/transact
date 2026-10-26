import type { ExtractionMethod, Recovery, RecoverySet, SamplingMethod, Surface } from '@/api/types'

export function surfaceLabel(surface?: Surface | null): string {
  if (!surface) return '—'
  const template = surface.surface_template
  const subject = surface.individual
    ? 'Individual'
    : (template?.item?.item_category?.name ?? 'Item')
  const part =
    surface.location_of_body_category?.name ??
    template?.location_of_body_category?.name ??
    surface.item_parts_category?.name ??
    template?.item_parts_category?.name ??
    null
  return [subject, part].filter(Boolean).join(' — ') || `Surface #${surface.id}`
}

export function recoverySetLabel(recoverySet?: RecoverySet | null): string {
  if (!recoverySet) return '—'
  return recoverySet.name || `Set #${recoverySet.id}`
}

export function extractionMethodLabel(method?: ExtractionMethod | null): string {
  if (!method) return '—'
  return method.extraction_protocol || `#${method.id}`
}

// A sampling method is a composite of (at most) one populated sub-method, so
// naming the sub-method that's actually set reads far better than the bare
// id ever could.
const samplingSubMethods: Array<{ key: keyof SamplingMethod; label: string }> = [
  { key: 'swab_method', label: 'Swab' },
  { key: 'tape_method', label: 'Tape' },
  { key: 'vacuum_method', label: 'Vacuum' },
  { key: 'cutting_method', label: 'Cutting' },
  { key: 'scraping_method', label: 'Scraping' },
  { key: 'picking_method', label: 'Picking' },
]

export function samplingMethodLabel(method?: SamplingMethod | null): string {
  if (!method) return '—'
  const match = samplingSubMethods.find((sub) => method[sub.key])
  return match?.label ?? `#${method.id}`
}

// Picking a recovery by its bare id is meaningless once there are more than
// a handful, so surface + recovery set + extraction method give enough
// detail to tell rows apart in a picker table.
export function recoveryLabel(recovery: Recovery): string {
  return surfaceLabel(recovery.surface)
}
