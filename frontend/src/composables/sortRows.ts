import type { TableSortMeta } from '@/api/types'

// Reads a dotted path such as "sample.surface.name" off a row.
export function resolveField(row: unknown, field: string): unknown {
  let value: unknown = row
  for (const key of field.split('.')) {
    if (value == null) return undefined
    value = (value as Record<string, unknown>)[key]
  }
  return value
}

const collator = new Intl.Collator(undefined, { numeric: true })

const isEmpty = (value: unknown) =>
  value == null || value === '' || (Array.isArray(value) && value.length === 0)

// Compares two cell values: text naturally ("Sample 2" before "Sample 10"),
// everything else by < and >. Empty values always go last, whatever the
// direction.
export function compareValues(a: unknown, b: unknown, order: 1 | -1): number {
  const emptyA = isEmpty(a)
  const emptyB = isEmpty(b)
  if (emptyA || emptyB) return emptyA === emptyB ? 0 : emptyA ? 1 : -1
  let result: number
  if (typeof a === 'string' && typeof b === 'string') result = collator.compare(a, b)
  else result = (a as number) < (b as number) ? -1 : (a as number) > (b as number) ? 1 : 0
  return result * order
}

// Sorts rows by one or more columns, so a CSV export lists rows in the order
// the table shows them. Array.prototype.sort is stable, so with no sort the
// rows keep their incoming order - as in the table. `accessors` reads a
// column's value where it isn't simply the field path.
export function sortRows<T>(
  rows: readonly T[],
  meta: readonly TableSortMeta[],
  accessors: Record<string, (row: T) => unknown> = {},
): T[] {
  const data = [...rows]
  if (!meta.length) return data
  const read = (row: T, field: string) =>
    accessors[field] ? accessors[field](row) : resolveField(row, field)
  return data.sort((a, b) => {
    for (const { field, order } of meta) {
      const result = compareValues(read(a, field), read(b, field), order)
      if (result !== 0) return result
    }
    return 0
  })
}
