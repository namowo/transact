<script setup lang="ts">
defineProps<{ names: string[] }>()
</script>

<template>
  <span v-if="names.length" class="flex flex-wrap gap-1">
    <UBadge v-for="name in names" :key="name" color="neutral" variant="subtle">{{ name }}</UBadge>
  </span>
  <span v-else>—</span>
</template>
