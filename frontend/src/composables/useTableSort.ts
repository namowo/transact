import { computed } from 'vue'
import { useToast } from '@nuxt/ui/composables'
import { updateMe } from '@/api/users'
import { useAuthStore } from '@/stores/auth'
import type { SortableTable, TableSortMeta } from '@/api/types'
import { sortRows } from './sortRows'
import { toSortMeta, toSortState, type SortState } from './useTableView'

export { sortRows }

// A table's column sort, saved on the user's
// profile so it is kept across studies and sessions. Until the user sorts,
// `defaults` applies.
export function useTableSort(table: SortableTable, defaults: TableSortMeta[] = []) {
  const auth = useAuthStore()
  const toast = useToast()

  const isCustom = computed(() => auth.user?.table_sorts?.[table] != null)

  const multiSortMeta = computed<TableSortMeta[]>({
    get: () => auth.user?.table_sorts?.[table] ?? defaults,
    set: (value) => save(value.map(({ field, order }) => ({ field, order }))),
  })

  // The same sort in UTable's shape, for useTableView.
  const sorting = computed<SortState[]>({
    get: () => toSortState(multiSortMeta.value),
    set: (value) => (multiSortMeta.value = toSortMeta(value)),
  })

  async function save(value: TableSortMeta[] | null) {
    const user = auth.user
    if (!user) return
    const tableSorts = { ...(user.table_sorts ?? {}) }
    if (value === null) delete tableSorts[table]
    else tableSorts[table] = value
    // Show the new order right away; the server copy follows.
    user.table_sorts = tableSorts
    try {
      await updateMe({ table_sorts: tableSorts })
    } catch {
      toast.add({
        color: 'error',
        title: 'Could not save the sort order',
        description: 'It applies until you reload the page.',
      })
    }
  }

  function resetSort() {
    return save(null)
  }

  return { multiSortMeta, sorting, isCustom, resetSort }
}
