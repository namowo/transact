<script setup lang="ts">
import { useRouter } from 'vue-router'
import Menu from 'primevue/menu'
import type { MenuItem } from 'primevue/menuitem'

const router = useRouter()

function toMenuItem(label: string, name: string): MenuItem {
  return { label, command: () => router.push({ name }) }
}

const menuItems: MenuItem[] = [
  toMenuItem('Extraction', 'settings-methods-extraction'),
  toMenuItem('PCR', 'settings-methods-pcr'),
  toMenuItem('CE', 'settings-methods-ce'),
  toMenuItem('Quantification', 'settings-methods-quantification'),
  toMenuItem('EPG Analysis', 'settings-methods-epg-analysis'),
  toMenuItem('EPG Interpretation', 'settings-methods-epg-interpretation'),
  toMenuItem('Post-PCR Treatment', 'settings-methods-post-pcr-treatment'),
  toMenuItem('Sampling', 'settings-methods-sampling'),
]
</script>

<template>
  <div class="flex flex-col gap-6 lg:flex-row lg:items-start">
    <Menu :model="menuItems" class="w-full lg:w-56 shrink-0" />
    <div class="flex-1 min-w-0">
      <router-view />
    </div>
  </div>
</template>
