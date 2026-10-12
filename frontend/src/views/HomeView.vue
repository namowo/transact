<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import DashboardView from '@/views/DashboardView.vue'
import StartpageView from '@/views/StartpageView.vue'

const auth = useAuthStore()
</script>

<template>
  <DashboardView v-if="auth.isAuthenticated" />
  <StartpageView v-else />
</template>
