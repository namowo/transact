import { nextTick, ref } from 'vue'
import { describe, expect, it } from 'vitest'
import { usePagination } from '../useTableView'

const numbers = (count: number) => Array.from({ length: count }, (_, i) => i + 1)

describe('usePagination', () => {
  it('shows 25 rows per page by default', () => {
    const pages = usePagination(numbers(53))
    expect(pages.rows).toEqual(numbers(25))
    expect(pages.total).toBe(53)
  })

  it('shows the rows of the chosen page', () => {
    const pages = usePagination(numbers(53))
    pages.page = 3
    expect(pages.rows).toEqual([51, 52, 53])
  })

  it('goes back to the first page when the page size or a reset source changes', async () => {
    const search = ref('')
    const pages = usePagination(numbers(60), 10, [search])
    pages.page = 4
    search.value = 'x'
    await nextTick()
    expect(pages.page).toBe(1)
    pages.page = 3
    pages.pageSize = 25
    await nextTick()
    expect(pages.page).toBe(1)
  })

  it('stays on a page that exists when rows go away', async () => {
    const rows = ref(numbers(70))
    const pages = usePagination(rows)
    pages.page = 3
    rows.value = numbers(30)
    await nextTick()
    expect(pages.page).toBe(2)
    expect(pages.rows).toEqual([26, 27, 28, 29, 30])
  })
})
