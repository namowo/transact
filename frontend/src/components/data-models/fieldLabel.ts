import type { CatalogField, FilterOp, PreviewColumn } from '@/api/types'

export function fieldLabel(field: Pick<CatalogField | PreviewColumn, 'label' | 'unit'>): string {
  return field.unit ? `${field.label} (${field.unit})` : field.label
}

export const operatorLabels: Record<FilterOp, string> = {
  eq: 'is',
  neq: 'is not',
  in: 'is one of',
  not_in: 'is none of',
  contains: 'contains',
  gt: 'greater than',
  gte: 'at least',
  lt: 'less than',
  lte: 'at most',
  between: 'between',
  is_null: 'is empty',
  not_null: 'is not empty',
}

export function operatorNeedsValue(op: FilterOp): boolean {
  return op !== 'is_null' && op !== 'not_null'
}

export function isListOperator(op: FilterOp): boolean {
  return op === 'in' || op === 'not_in'
}

/** Formats a cell value for display in the preview table. */
export function formatCell(value: unknown, type: string): string {
  if (value === null || value === undefined || value === '') return ''
  if (type === 'boolean' || typeof value === 'boolean') return value ? 'yes' : 'no'
  if (typeof value === 'number') {
    return Number.isInteger(value)
      ? String(value)
      : value.toLocaleString(undefined, { maximumFractionDigits: 6 })
  }
  if (type === 'date' && typeof value === 'string') {
    const date = new Date(value)
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
  }
  return String(value)
}
