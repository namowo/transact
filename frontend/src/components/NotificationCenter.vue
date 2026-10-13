<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { DropdownMenuItem } from '@nuxt/ui'
import { useAuthStore } from '@/stores/auth'
import { usePendingRequests } from '@/composables/usePendingRequests'

const auth = useAuthStore()
const router = useRouter()
const { labRequests, newLabRequests, totalCount, load } = usePendingRequests()

onMounted(load)

const items = computed<DropdownMenuItem[][]>(() => {
  const groups: DropdownMenuItem[][] = []

  if (labRequests.value.length > 0) {
    groups.push(
      labRequests.value.map((r) => ({
        label: `${r.user.first_name} ${r.user.last_name} wants to join`,
        description: r.laboratory.laboratory_name,
        icon: 'i-lucide-user-plus',
        onSelect: () => router.push({ name: 'lab-users' }),
      })),
    )
  }

  if (newLabRequests.value.length > 0) {
    groups.push(
      newLabRequests.value.map((r) => ({
        label: `New laboratory: ${r.laboratory.laboratory_name}`,
        description: `${r.user.first_name} ${r.user.last_name}`,
        icon: 'i-lucide-building-2',
        onSelect: () => router.push({ name: 'laboratories' }),
      })),
    )
  }

  if (groups.length === 0) {
    groups.push([
      { label: "You're all caught up", icon: 'i-lucide-check', disabled: true },
    ])
  }

  return groups
})
</script>

<template>
  <UDropdownMenu
    v-if="auth.isLabAdmin || auth.isSuperuser"
    :items="items"
    :content="{ align: 'end' }"
    :ui="{ content: 'w-80' }"
    @update:open="(open: boolean) => open && load()"
  >
    <UTooltip text="Notifications">
      <UChip :show="totalCount > 0" :text="totalCount" color="error" size="lg">
        <UButton
          icon="i-lucide-bell"
          variant="ghost"
          color="neutral"
          square
          aria-label="Notifications"
        />
      </UChip>
    </UTooltip>
  </UDropdownMenu>
</template>
