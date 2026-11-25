import { h } from 'vue'
import UButton from '@nuxt/ui/components/Button.vue'
import type { CellContext, HeaderContext } from '@tanstack/vue-table'

// A sortable UTable column header. A click sorts by the column - ascending,
// then descending, then not at all. With `multi`, Shift-, Ctrl- or ⌘-click
// adds the column to the current sort instead of replacing it.
export function sortHeader(label: string, { multi = false }: { multi?: boolean } = {}) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- fits any row type
  return ({ column, table }: HeaderContext<any, unknown>) => {
    const sorting = table.getState().sorting ?? []
    const index = sorting.findIndex((s) => s.id === column.id)
    const current = sorting[index]

    function toggle(event: MouseEvent) {
      const next = !current
        ? { id: column.id, desc: false }
        : !current.desc
          ? { id: column.id, desc: true }
          : null
      if (multi && (event.shiftKey || event.metaKey || event.ctrlKey)) {
        const list = [...sorting]
        if (index === -1) list.push(next!)
        else if (next) list[index] = next
        else list.splice(index, 1)
        table.setSorting(list)
      } else {
        table.setSorting(next ? [next] : [])
      }
    }

    return h(
      UButton,
      {
        color: 'neutral',
        variant: 'ghost',
        size: 'sm',
        label,
        trailingIcon: current
          ? current.desc
            ? 'i-lucide-arrow-down-wide-narrow'
            : 'i-lucide-arrow-up-narrow-wide'
          : 'i-lucide-arrow-up-down',
        class: ['-mx-2.5 font-semibold', current ? 'text-highlighted' : 'text-toned'],
        onClick: toggle,
      },
      multi && sorting.length > 1 && current
        ? { trailing: () => h('span', { class: 'text-xs tabular-nums text-muted' }, index + 1) }
        : undefined,
    )
  }
}

// A narrow first column with a chevron that shows or hides the row's
// `#expanded` slot. Pair with `v-model:expanded` and `get-row-id`.
export function expandColumn(id = 'expand') {
  return {
    id,
    header: '',
    meta: { class: { td: 'w-10', th: 'w-10' } },
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- fits any row type
    cell: ({ row }: CellContext<any, unknown>) =>
      h(UButton, {
        color: 'neutral',
        variant: 'ghost',
        size: 'sm',
        square: true,
        icon: 'i-lucide-chevron-right',
        'aria-label': row.getIsExpanded() ? 'Collapse row' : 'Expand row',
        'aria-expanded': row.getIsExpanded(),
        ui: { leadingIcon: ['transition-transform', row.getIsExpanded() ? 'rotate-90' : ''] },
        onClick: () => row.toggleExpanded(),
      }),
  }
}
