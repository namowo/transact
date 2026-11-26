<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { getErrorMessage } from '@/api/errors'
import { listMyNotificationTypes } from '@/api/users'
import type { NotificationChannel, NotificationTypeInfo, NotificationTypeKey } from '@/api/types'
import { useBrowserNotifications } from '@/composables/useBrowserNotifications'

const auth = useAuthStore()
const browser = useBrowserNotifications()
browser.refreshPermission()

const channels: { key: NotificationChannel; label: string }[] = [
  { key: 'email', label: 'Email' },
  { key: 'browser', label: 'Browser' },
]

// Only the types the user's permissions let them receive.
const types = ref<NotificationTypeInfo[]>([])
const loading = ref(true)
const errorMessage = ref('')
const saving = ref<string | null>(null)

onMounted(async () => {
  try {
    types.value = await listMyNotificationTypes()
  } catch (err) {
    errorMessage.value = getErrorMessage(err, 'Could not load your notification settings.')
  } finally {
    loading.value = false
  }
})

function isOn(type: NotificationTypeKey, channel: NotificationChannel) {
  return auth.user?.notification_settings[type]?.[channel] ?? false
}

const anyBrowserOn = computed(() =>
  types.value.some((t) => t.channels.includes('browser') && isOn(t.key, 'browser')),
)

async function ensureBrowserPermission() {
  if (browser.permission.value === 'granted') return true
  if ((await browser.requestPermission()) === 'granted') return true
  errorMessage.value = 'Your browser did not allow notifications for this site.'
  return false
}

async function toggle(type: NotificationTypeKey, channel: NotificationChannel, value: boolean) {
  errorMessage.value = ''
  if (value && channel === 'browser' && !(await ensureBrowserPermission())) return

  saving.value = `${type}.${channel}`
  try {
    await auth.updateProfile({ notification_settings: { [type]: { [channel]: value } } })
  } catch (err) {
    errorMessage.value = getErrorMessage(err, 'Could not save your notification settings.')
  } finally {
    saving.value = null
  }
}

async function allowInThisBrowser() {
  errorMessage.value = ''
  await ensureBrowserPermission()
}

function sendTest() {
  browser.show('Notifications are on', {
    body: 'This is how TransAct will let you know about new requests.',
  })
}
</script>

<template>
  <UCard>
    <template #header>
      <h2 class="text-lg font-semibold text-highlighted">Notifications</h2>
      <p class="text-sm text-muted">
        Choose what you hear about, and how. You only see notifications your permissions apply to.
      </p>
    </template>

    <div class="flex flex-col gap-6">
      <div v-if="loading" class="flex flex-col gap-3">
        <USkeleton v-for="i in 2" :key="i" class="h-12 w-full" />
      </div>

      <UAlert
        v-else-if="types.length === 0 && !errorMessage"
        color="neutral"
        variant="subtle"
        icon="i-lucide-bell-off"
        description="There's nothing to notify you about with your current permissions. Notifications appear here once you review requests or enter data for a laboratory."
      />

      <div v-else-if="types.length > 0" class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-default">
              <th class="py-2 pe-4 text-start font-medium text-muted">Notify me when…</th>
              <th
                v-for="channel in channels"
                :key="channel.key"
                class="w-24 py-2 text-center font-medium text-muted"
              >
                {{ channel.label }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="type in types" :key="type.key" class="border-b border-default last:border-b-0">
              <td class="py-3 pe-4">
                <div class="font-medium text-highlighted">{{ type.label }}</div>
                <div class="text-muted">{{ type.description }}</div>
              </td>
              <td v-for="channel in channels" :key="channel.key" class="py-3 text-center">
                <USwitch
                  v-if="type.channels.includes(channel.key)"
                  :model-value="isOn(type.key, channel.key)"
                  :loading="saving === `${type.key}.${channel.key}`"
                  :disabled="channel.key === 'browser' && !browser.supported"
                  :aria-label="`${type.label}: ${channel.label}`"
                  class="inline-flex"
                  @update:model-value="(value: boolean) => toggle(type.key, channel.key, value)"
                />
                <UTooltip v-else :text="`Not available by ${channel.label.toLowerCase()}`">
                  <span class="text-dimmed" :aria-label="`Not available by ${channel.label.toLowerCase()}`">—</span>
                </UTooltip>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <template v-if="types.some((t) => t.channels.includes('browser'))">
        <UAlert
          v-if="!browser.supported"
          color="warning"
          variant="subtle"
          description="This browser doesn't support notifications."
        />
        <UAlert
          v-else-if="anyBrowserOn && browser.permission.value === 'denied'"
          color="warning"
          variant="subtle"
          description="Notifications are blocked for this site in this browser. Allow them in your browser's site settings to receive them here."
        />
        <UAlert
          v-else-if="anyBrowserOn && browser.permission.value === 'default'"
          color="info"
          variant="subtle"
          description="Browser notifications are on for your account, but this browser hasn't been allowed to show them yet."
          :actions="[{ label: 'Allow in this browser', onClick: allowInThisBrowser }]"
        />
        <div v-else-if="anyBrowserOn" class="flex flex-wrap items-center gap-3">
          <UButton
            label="Send a test notification"
            icon="i-lucide-bell-ring"
            color="neutral"
            variant="outline"
            size="sm"
            @click="sendTest"
          />
        </div>
        <p class="text-xs text-muted">
          Browser notifications show while TransAct is open in a tab, and need to be allowed once in
          each browser.
        </p>
      </template>

      <UAlert v-if="errorMessage" color="error" variant="outline" :description="errorMessage" />

      <p class="text-xs text-muted">
        Emails about your own account, like password resets and the outcome of your own requests,
        are always sent.
      </p>
    </div>
  </UCard>
</template>
