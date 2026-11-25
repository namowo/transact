<script setup lang="ts">
import type { User } from '@/api/types'

defineProps<{ user: User }>()
</script>

<template>
  <div class="flex flex-wrap gap-1">
    <UBadge
      v-for="group in user.groups"
      :key="group.id"
      :label="group.name"
      :color="group.system_key === 'administrator' ? 'primary' : 'neutral'"
      :variant="group.laboratory_id ? 'outline' : 'subtle'"
      size="sm"
    />
    <span v-if="!user.groups.length" class="text-xs text-muted">—</span>
  </div>
</template>
