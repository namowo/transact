import type { ContactTemplate, Surface, SurfaceTemplate } from '@/api/types'

export function surfaceLabel(surface?: SurfaceTemplate | null): string {
  if (!surface) return '—'
  if (surface.item) {
    const category = surface.item.item_category?.name
    return category ? `Item (${category})` : 'Item'
  }
  const part = surface.location_of_body_category?.name
  return part ? `Individual (${part})` : 'Individual'
}

export function surfaceIcon(surface?: SurfaceTemplate | null): string | null {
  if (!surface) return null
  return surface.item ? 'i-lucide-package' : 'i-lucide-user'
}

// Short detail for table columns, where an icon already conveys item vs.
// individual - repeating that word would be noise.
export function surfaceDetail(surface?: SurfaceTemplate | null): string {
  if (!surface) return '—'
  if (surface.item) return surface.item.item_category?.name ?? '—'
  return surface.location_of_body_category?.name ?? '—'
}

export function templateName(template: ContactTemplate): string {
  if (template.name) return template.name
  const donor = surfaceLabel(template.donor_surface_template)
  const recipient = surfaceLabel(template.recipient_surface_template)
  return `${donor} → ${recipient}`
}

// Icon/detail for an actual Contact's realized Surface (individual or item),
// as opposed to a template's SurfaceTemplate slot.
export function surfaceInstanceIcon(surface?: Surface | null): string | null {
  if (!surface) return null
  return surface.individual ? 'i-lucide-user' : 'i-lucide-package'
}

export function surfaceInstanceDetail(surface?: Surface | null, individualLabel?: string | null): string {
  if (!surface) return '—'
  if (surface.individual) return individualLabel ?? 'Individual'
  const category = surface.surface_template?.item?.item_category?.name
  return category ?? 'Item'
}
