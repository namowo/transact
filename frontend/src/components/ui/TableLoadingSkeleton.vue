<script setup lang="ts">
// Placeholder rows for a UTable's #loading slot (shown while loading with no rows yet).
withDefaults(defineProps<{ rows?: number }>(), { rows: 5 })
</script>

<template>
  <div class="flex flex-col gap-3" aria-hidden="true">
    <USkeleton v-for="row in rows" :key="row" class="h-6 w-full" />
  </div>
</template>
