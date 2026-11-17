import { localeComparator, resolveFieldData, sort } from '@openuxkit/utils/object'
import type { TableSortMeta } from '@/api/types'

// Sorts rows exactly like an openvue DataTable with sortMode="multiple" (same
// helpers, same tie-breaking), so a CSV export lists rows in the order the
// table shows them. Array.prototype.sort is stable, so with no sort the rows
// keep their incoming order - as in the table.
export function sortRows<T>(rows: readonly T[], meta: readonly TableSortMeta[]): T[] {
  const data = [...rows]
  if (!meta.length) return data
  const comparer = localeComparator()
  const compareAt = (a: T, b: T, index: number): number => {
    const { field, order } = meta[index]!
    const value1 = resolveFieldData(a, field)
    const value2 = resolveFieldData(b, field)
    if (value1 === value2) return index < meta.length - 1 ? compareAt(a, b, index + 1) : 0
    return sort(value1, value2, order, comparer, 1)
  }
  return data.sort((a, b) => compareAt(a, b, 0))
}
