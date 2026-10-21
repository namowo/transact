<script setup lang="ts">
withDefaults(defineProps<{ columns?: number; rows?: number }>(), {
  columns: 4,
  rows: 6,
})
</script>

<template>
  <div class="flex flex-col gap-3">
    <div class="flex gap-4">
      <USkeleton v-for="col in columns" :key="`head-${col}`" class="h-4 flex-1" />
    </div>
    <div v-for="row in rows" :key="`row-${row}`" class="flex gap-4">
      <USkeleton v-for="col in columns" :key="`cell-${row}-${col}`" class="h-8 flex-1" />
    </div>
  </div>
</template>
