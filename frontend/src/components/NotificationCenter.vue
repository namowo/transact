<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { DropdownMenuItem } from '@nuxt/ui'
import { useAuthStore } from '@/stores/auth'
import { usePendingRequests } from '@/composables/usePendingRequests'
import { useBrowserNotifications } from '@/composables/useBrowserNotifications'

const POLL_INTERVAL_MS = 60_000

const auth = useAuthStore()
const router = useRouter()
const { labRequests, newLabRequests, totalCount, load } = usePendingRequests()
const browserNotifications = useBrowserNotifications()

const isReviewer = computed(() => auth.isLabAdmin || auth.can('laboratories.manage'))

// Requests already known in this tab. The first load only fills it, so
// requests that were waiting before the app was opened don't all pop up at
// once (they show in the bell, and were emailed if the user wants emails).
// The requests listed already depend on the user's permissions; each type
// is shown only if the user turned on browser notifications for it.
let seen: Set<string> | null = null

function notifyAboutNew() {
  const current = [
    ...labRequests.value.map((r) => ({
      id: r.id,
      type: 'lab_membership_request' as const,
      title: `${r.user.first_name} ${r.user.last_name} wants to join`,
      body: r.laboratory.laboratory_name,
      route: 'lab-users',
    })),
    ...newLabRequests.value.map((r) => ({
      id: r.id,
      type: 'laboratory_request' as const,
      title: `New laboratory: ${r.laboratory.laboratory_name}`,
      body: `Requested by ${r.user.first_name} ${r.user.last_name}`,
      route: 'laboratories',
    })),
  ]
  const previous = seen
  seen = new Set(current.map((r) => r.id))
  if (!previous) return

  for (const request of current) {
    if (previous.has(request.id)) continue
    if (!auth.user?.notification_settings[request.type]?.browser) continue
    browserNotifications.show(request.title, {
      body: request.body,
      tag: `request-${request.id}`,
      onClick: () => router.push({ name: request.route }),
    })
  }
}

async function refresh() {
  if (!isReviewer.value) return
  await load()
  notifyAboutNew()
}

let timer: ReturnType<typeof setInterval> | undefined

function onVisibilityChange() {
  if (document.visibilityState === 'visible') refresh()
}

onMounted(() => {
  refresh()
  timer = setInterval(refresh, POLL_INTERVAL_MS)
  document.addEventListener('visibilitychange', onVisibilityChange)
})

onBeforeUnmount(() => {
  clearInterval(timer)
  document.removeEventListener('visibilitychange', onVisibilityChange)
})

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
    groups.push([{ label: "You're all caught up", icon: 'i-lucide-check', disabled: true }])
  }

  return groups
})
</script>

<template>
  <UDropdownMenu
    v-if="isReviewer"
    :items="items"
    :content="{ align: 'end' }"
    :ui="{ content: 'w-80' }"
    @update:open="(open: boolean) => open && refresh()"
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
