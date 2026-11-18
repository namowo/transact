<script setup lang="ts">
import { computed } from 'vue'
import type { CatalogDataset, CatalogTable } from '@/api/types'

const props = defineProps<{
  dataset: CatalogDataset
  joins: string[]
  // Selected column keys, to show how many come from each table.
  columns: string[]
}>()

const emit = defineEmits<{ toggle: [key: string, on: boolean] }>()

const joined = computed(() => new Set(props.joins))
const labels = computed(() => new Map(props.dataset.tables.map((t) => [t.key, t.label])))

const required = computed(() => props.dataset.tables.filter((t) => t.required))
const optional = computed(() => props.dataset.tables.filter((t) => !t.required))

const columnCounts = computed(() => {
  const tableOf = new Map(props.dataset.fields.map((f) => [f.key, f.table]))
  const counts = new Map<string, number>()
  for (const key of props.columns) {
    const table = tableOf.get(key)
    if (table) counts.set(table, (counts.get(table) ?? 0) + 1)
  }
  return counts
})

function requiresText(table: CatalogTable) {
  const names = table.requires
    .filter((key) => !props.dataset.tables.find((t) => t.key === key)?.required)
    .map((key) => labels.value.get(key) ?? key)
  return names.length ? `Also joins ${names.join(', ')}.` : ''
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-col gap-1.5">
      <span class="text-xs font-medium uppercase tracking-wide text-muted">Always included</span>
      <div class="flex flex-wrap gap-1.5">
        <UTooltip v-for="table in required" :key="table.key" :text="table.description">
          <UBadge
            :label="
              columnCounts.get(table.key)
                ? `${table.label} · ${columnCounts.get(table.key)}`
                : table.label
            "
            color="neutral"
            variant="subtle"
            icon="i-lucide-lock"
          />
        </UTooltip>
      </div>
    </div>

    <div v-if="optional.length" class="flex flex-col gap-2">
      <span class="text-xs font-medium uppercase tracking-wide text-muted">Join tables</span>
      <div class="grid gap-x-6 gap-y-3 md:grid-cols-2 xl:grid-cols-3">
        <div v-for="table in optional" :key="table.key" class="flex items-start gap-2">
          <UCheckbox
            :model-value="joined.has(table.key)"
            :label="table.label"
            :description="[table.description, requiresText(table)].filter(Boolean).join(' ')"
            class="flex-1"
            @update:model-value="
              (on: boolean | 'indeterminate') => emit('toggle', table.key, on === true)
            "
          />
          <UBadge
            v-if="columnCounts.get(table.key)"
            :label="`${columnCounts.get(table.key)} ${columnCounts.get(table.key) === 1 ? 'column' : 'columns'}`"
            size="sm"
            variant="subtle"
          />
        </div>
      </div>
    </div>
  </div>
</template>
