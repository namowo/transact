<script setup lang="ts">
import GroupsManager from '@/components/groups/GroupsManager.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <div class="flex flex-col gap-6">
    <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Laboratory Groups</h1>
    <GroupsManager v-if="auth.user?.laboratory_id" :laboratory-id="auth.user.laboratory_id" />
  </div>
</template>
