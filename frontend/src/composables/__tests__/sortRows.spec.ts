import { describe, expect, it } from 'vitest'
import { sortRows } from '../sortRows'

const rows = [
  { id: 1, scenario: 'B', name: 'Sample 10', volume: 5 },
  { id: 2, scenario: 'A', name: 'Sample 2', volume: null },
  { id: 3, scenario: 'B', name: 'Sample 2', volume: 1 },
  { id: 4, scenario: 'A', name: null, volume: 3 },
]

const ids = (list: { id: number }[]) => list.map((row) => row.id)

describe('sortRows', () => {
  it('keeps the incoming order without a sort', () => {
    expect(ids(sortRows(rows, []))).toEqual([1, 2, 3, 4])
  })

  it('sorts by several columns, numbers inside text naturally', () => {
    const sorted = sortRows(rows, [
      { field: 'scenario', order: 1 },
      { field: 'name', order: 1 },
    ])
    expect(ids(sorted)).toEqual([2, 4, 3, 1])
  })

  it('honours descending order', () => {
    expect(ids(sortRows(rows, [{ field: 'volume', order: -1 }]))).toEqual([1, 4, 3, 2])
  })

  it('does not change the input', () => {
    sortRows(rows, [{ field: 'name', order: 1 }])
    expect(ids(rows)).toEqual([1, 2, 3, 4])
  })
})
