<script setup lang="ts">
import { computed } from 'vue'
import type { TableColumn } from '@nuxt/ui'
import type { DataModelPreview } from '@/api/types'
import { fieldLabel, formatCell } from './fieldLabel'
import TableLoadingSkeleton from '@/components/ui/TableLoadingSkeleton.vue'
import { usePagination } from '@/composables/useTableView'
import TablePagination from '@/components/ui/TablePagination.vue'

const props = defineProps<{
  preview: DataModelPreview | null
  loading: boolean
  error: string | null
  // The model changed since the preview was loaded.
  stale: boolean
  skippedFilters: number
}>()

const open = defineModel<boolean>('open', { required: true })
const emit = defineEmits<{ run: [] }>()

type Row = Record<string, string>

const columns = computed<TableColumn<Row>[]>(() =>
  (props.preview?.columns ?? []).map((column, index) => ({
    accessorKey: `c${index}`,
    header: fieldLabel(column),
    meta: {
      class: {
        td: column.type === 'number' ? 'text-right tabular-nums' : 'max-w-80 truncate',
        th: column.type === 'number' ? 'text-right' : '',
      },
    },
  })),
)

const data = computed<Row[]>(() => {
  const preview = props.preview
  if (!preview) return []
  return preview.rows.map((row) =>
    Object.fromEntries(
      row.map((value, index) => [
        `c${index}`,
        formatCell(value, preview.columns[index]?.type ?? ''),
      ]),
    ),
  )
})

const dataPages = usePagination(data)

const summary = computed(() => {
  const preview = props.preview
  if (!preview) return null
  const rows = preview.total_rows.toLocaleString()
  const studies = preview.study_count
  return `${rows} ${preview.total_rows === 1 ? 'row' : 'rows'} from ${studies} ${studies === 1 ? 'study' : 'studies'}`
})

function refresh() {
  open.value = true
  emit('run')
}

function show() {
  open.value = true
  if (!props.preview || props.stale) emit('run')
}
</script>

<template>
  <section
    class="sticky bottom-0 z-10 rounded-t-lg border border-b-0 border-default bg-default shadow-lg"
    aria-label="Data preview"
  >
    <div class="flex flex-wrap items-center gap-2 px-3 py-2">
      <UButton
        variant="ghost"
        color="neutral"
        :icon="open ? 'i-lucide-chevron-down' : 'i-lucide-chevron-up'"
        :label="open ? 'Hide preview' : 'Show preview'"
        :aria-expanded="open"
        @click="open ? (open = false) : show()"
      />
      <span v-if="summary" class="text-sm font-medium">{{ summary }}</span>
      <span
        v-if="preview && open && preview.total_rows > preview.rows.length"
        class="text-sm text-muted"
      >
        · first {{ preview.rows.length }} shown
      </span>
      <UBadge
        v-if="preview && stale"
        color="warning"
        variant="subtle"
        icon="i-lucide-clock-alert"
        label="Outdated"
      />
      <UBadge
        v-if="skippedFilters"
        color="warning"
        variant="subtle"
        :label="`${skippedFilters} incomplete ${skippedFilters === 1 ? 'filter' : 'filters'} ignored`"
      />
      <UButton
        class="ms-auto"
        size="sm"
        :variant="preview && !stale ? 'ghost' : 'soft'"
        :color="preview && !stale ? 'neutral' : 'primary'"
        icon="i-lucide-refresh-cw"
        :label="preview ? 'Refresh' : 'Load preview'"
        :loading="loading"
        @click="refresh"
      />
    </div>

    <div v-if="open" class="border-t border-default p-3">
      <UAlert
        v-if="error"
        color="error"
        variant="subtle"
        icon="i-lucide-circle-alert"
        :description="error"
      />
      <UEmpty
        v-else-if="preview && !preview.total_rows"
        icon="i-lucide-table"
        title="No rows match"
        description="Try removing filters or including more studies. Only published, quality-checked studies - and your laboratory's own, when signed in - are available."
        variant="naked"
        size="sm"
      />
      <template v-else>
        <UTable
          :data="dataPages.rows"
          :columns="columns"
          :loading="loading && !preview"
          sticky
          class="max-h-[40vh] rounded-md border border-default"
          :ui="{ td: 'py-2 text-sm whitespace-nowrap', th: 'whitespace-nowrap' }"
        >
          <template #loading>
            <TableLoadingSkeleton />
          </template>
        </UTable>
        <TablePagination
          v-model:page="dataPages.page"
          v-model:page-size="dataPages.pageSize"
          :total="dataPages.total"
        />
      </template>
    </div>
  </section>
</template>
