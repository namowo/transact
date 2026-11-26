<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'

const menuItems: NavigationMenuItem[] = [
  { label: 'Profile', icon: 'i-lucide-user', to: { name: 'profile' }, exact: true },
  { label: 'Email & password', icon: 'i-lucide-key-round', to: { name: 'profile-sign-in' } },
  {
    label: 'Two-factor authentication',
    icon: 'i-lucide-shield-check',
    to: { name: 'profile-two-factor' },
  },
  { label: 'Passkeys', icon: 'i-lucide-fingerprint', to: { name: 'profile-passkeys' } },
  { label: 'API keys', icon: 'i-lucide-code', to: { name: 'profile-api-keys' } },
  { label: 'Notifications', icon: 'i-lucide-bell', to: { name: 'profile-notifications' } },
]
</script>

<template>
  <div class="flex flex-col gap-6 lg:flex-row lg:items-start">
    <UNavigationMenu :items="menuItems" orientation="vertical" class="w-full lg:w-56 shrink-0" />
    <div class="flex-1 min-w-0 max-w-2xl">
      <router-view />
    </div>
  </div>
</template>
