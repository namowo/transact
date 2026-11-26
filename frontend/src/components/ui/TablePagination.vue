<script setup lang="ts">
import { computed } from 'vue'

// Page controls under a table: which rows are shown, how many per page, and
// the page buttons.
const props = withDefaults(defineProps<{ total: number; pageSizes?: number[] }>(), {
  pageSizes: () => [25, 50, 100, 200],
})

const page = defineModel<number>('page', { required: true })
const pageSize = defineModel<number>('pageSize', { required: true })

const range = computed(() => {
  if (!props.total) return '0 rows'
  const first = (page.value - 1) * pageSize.value + 1
  const last = Math.min(props.total, page.value * pageSize.value)
  return `${first}–${last} of ${props.total}`
})
</script>

<template>
  <!-- Shown whenever there are rows, even if they fit on one page, so the
       row count and page size are always at hand. -->
  <div v-if="total > 0" class="flex flex-wrap items-center justify-between gap-3 pt-3">
    <div class="flex items-center gap-2 text-sm text-muted">
      <span class="tabular-nums">{{ range }}</span>
      <span aria-hidden="true">·</span>
      <USelect
        v-model="pageSize"
        :items="pageSizes.map((size) => ({ label: `${size} per page`, value: size }))"
        size="sm"
        variant="ghost"
        class="w-34"
        aria-label="Rows per page"
      />
    </div>
    <UPagination
      v-model:page="page"
      :items-per-page="pageSize"
      :total="total"
      size="sm"
      show-edges
    />
  </div>
</template>
