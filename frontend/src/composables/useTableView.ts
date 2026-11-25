import { computed, reactive, ref, toValue, watch, type MaybeRefOrGetter, type Ref } from 'vue'
import type { TableSortMeta } from '@/api/types'
import { resolveField, sortRows } from './sortRows'

// A column sort as Nuxt UI's UTable (TanStack) keeps it.
export interface SortState {
  id: string
  desc: boolean
}

export const toSortMeta = (sorting: readonly SortState[]): TableSortMeta[] =>
  sorting.map(({ id, desc }) => ({ field: id, order: desc ? -1 : 1 }))

export const toSortState = (meta: readonly TableSortMeta[]): SortState[] =>
  meta.map(({ field, order }) => ({ id: field, desc: order === -1 }))

// How a value is read off a row: a dotted field path or a function.
type Accessor<T> = string | ((row: T) => unknown)

// 'contains' matches text case-insensitively, 'equals' matches the value
// exactly (booleans, ids, select options).
export interface TableFilter<T> {
  field: Accessor<T>
  mode?: 'contains' | 'equals'
}

export interface TableViewOptions<T, F extends string> {
  // Fields the search box looks in.
  searchFields?: Accessor<T>[]
  // Filters offered in the filter drawer, by name.
  filters?: Record<F, TableFilter<T>>
  // The sort; pass a ref to keep it elsewhere (e.g. on the user's profile).
  sorting?: Ref<SortState[]> | SortState[]
  // Where a sort column's value is when the column id is not its field path.
  sortAccessors?: Record<string, Accessor<T>>
  // Reads any other sort column's value; by default its id is a field path.
  sortValue?: (row: T, id: string) => unknown
  // Rows per page; leave out to show every row.
  pageSize?: number
}

const read = <T>(row: T, accessor: Accessor<T>) =>
  typeof accessor === 'function' ? accessor(row) : resolveField(row, accessor)

const asText = (value: unknown): string =>
  value == null ? '' : Array.isArray(value) ? value.map(asText).join(', ') : String(value)

// Filter values come from inputs, selects and switches alike.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type FilterValue = any

const isActive = (value: unknown) =>
  value != null && value !== '' && !(Array.isArray(value) && !value.length)

// The rows that contain `term` in any of `fields`, ignoring case.
export function searchRows<T>(rows: readonly T[], fields: Accessor<T>[], term: string): T[] {
  const needle = term.trim().toLocaleLowerCase()
  if (!needle) return [...rows]
  return rows.filter((row) =>
    fields.some((field) => asText(read(row, field)).toLocaleLowerCase().includes(needle)),
  )
}

// Search, filters, sort and pagination for a UTable over rows held in
// memory. Pass `rows` to the table along with
// `v-model:sorting="view.sorting"` and `:sorting-options="manualSorting"`.
export function useTableView<T, F extends string = never>(
  source: MaybeRefOrGetter<readonly T[] | null | undefined>,
  options: TableViewOptions<T, F> = {},
) {
  const search = ref('')
  const filterDefs = (options.filters ?? {}) as Record<F, TableFilter<T>>
  const filterNames = Object.keys(filterDefs) as F[]
  const filters = reactive(Object.fromEntries(filterNames.map((name) => [name, null]))) as Record<
    F,
    FilterValue
  >
  const sorting: Ref<SortState[]> =
    options.sorting && !Array.isArray(options.sorting)
      ? options.sorting
      : ref(options.sorting ?? [])

  const activeFilterCount = computed(
    () => filterNames.filter((name) => isActive(filters[name])).length,
  )

  function resetFilters() {
    for (const name of filterNames) filters[name] = null
  }

  function reset() {
    search.value = ''
    resetFilters()
  }

  const filteredRows = computed(() => {
    const rows = toValue(source) ?? []
    const term = search.value.trim().toLocaleLowerCase()
    const active = filterNames.filter((name) => isActive(filters[name]))
    if (!term && !active.length) return [...rows]
    const matching = rows.filter((row) => {
      for (const name of active) {
        const { field, mode = 'contains' } = filterDefs[name]
        const wanted = filters[name]
        const value = read(row, field)
        if (mode === 'equals') {
          if (Array.isArray(wanted) ? !wanted.includes(value) : value !== wanted) return false
        } else if (
          !asText(value).toLocaleLowerCase().includes(String(wanted).toLocaleLowerCase())
        ) {
          return false
        }
      }
      return true
    })
    return term ? searchRows(matching, options.searchFields ?? [], term) : matching
  })

  const sortedRows = computed(() => {
    const accessors: Record<string, (row: T) => unknown> = {}
    for (const { id } of sorting.value) {
      const accessor = options.sortAccessors?.[id]
      if (accessor) accessors[id] = (row) => read(row, accessor)
      else if (options.sortValue) accessors[id] = (row) => options.sortValue!(row, id)
    }
    return sortRows(filteredRows.value, toSortMeta(sorting.value), accessors)
  })

  const page = ref(1)
  const pageSize = ref(options.pageSize ?? 0)
  const total = computed(() => sortedRows.value.length)

  // A new search or filter starts over on the first page.
  watch([search, () => ({ ...filters }), pageSize], () => (page.value = 1))
  // Stay on a page that exists when rows go away.
  watch(total, (count) => {
    const last = Math.max(1, Math.ceil(count / (pageSize.value || count || 1)))
    if (page.value > last) page.value = last
  })

  const rows = computed(() => {
    if (!pageSize.value) return sortedRows.value
    const start = (page.value - 1) * pageSize.value
    return sortedRows.value.slice(start, start + pageSize.value)
  })

  return reactive({
    search,
    filters,
    activeFilterCount,
    resetFilters,
    reset,
    sorting,
    filteredRows,
    sortedRows,
    rows,
    page,
    pageSize,
    total,
  })
}

// UTable sorts nothing itself; useTableView hands it sorted rows.
export const manualSorting = { manualSorting: true }
