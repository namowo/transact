<script setup lang="ts">
import Card from 'primevue/card'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <div class="flex flex-col gap-6">
    <div>
      <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">
        Welcome, {{ auth.user?.first_name }}
      </h1>
      <p class="text-surface-600 dark:text-surface-300">
        {{ auth.user?.laboratory?.laboratory_name }}
      </p>
    </div>

    <Card>
      <template #title>Your account</template>
      <template #content>
        <dl class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <dt class="text-sm text-surface-500">Name</dt>
            <dd class="text-surface-900 dark:text-surface-0">
              {{ auth.user?.first_name }} {{ auth.user?.last_name }}
            </dd>
          </div>
          <div>
            <dt class="text-sm text-surface-500">Email</dt>
            <dd class="text-surface-900 dark:text-surface-0">{{ auth.user?.email }}</dd>
          </div>
          <div>
            <dt class="text-sm text-surface-500">Laboratory</dt>
            <dd class="text-surface-900 dark:text-surface-0">
              {{ auth.user?.laboratory?.laboratory_name }}
            </dd>
          </div>
        </dl>
      </template>
    </Card>
  </div>
</template>
