<script setup lang="ts">
import GroupsManager from '@/components/groups/GroupsManager.vue'
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Groups &amp; Permissions</h1>
      <p class="text-sm text-muted">
        Groups bundle permissions; users get everything their groups grant. Assign groups on the
        Users page.
      </p>
    </div>
    <GroupsManager />
  </div>
</template>
