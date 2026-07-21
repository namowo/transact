<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Card from 'primevue/card'
import Message from 'primevue/message'
import Button from 'primevue/button'
import { useAuthStore } from '@/stores/auth'
import * as webauthnApi from '@/api/webauthn'

const auth = useAuthStore()
const router = useRouter()

const showPasskeyBanner = ref(false)

onMounted(async () => {
  if (auth.user && !auth.user.passkey_prompt_dismissed) {
    const credentials = await webauthnApi.listCredentials().catch(() => [])
    showPasskeyBanner.value = credentials.length === 0
  }
})

function onSetUpPasskey() {
  showPasskeyBanner.value = false
  auth.dismissPasskeyPromptBanner()
  router.push({ name: 'profile' })
}

function onDismissPasskeyBanner() {
  showPasskeyBanner.value = false
  auth.dismissPasskeyPromptBanner()
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <Message v-if="showPasskeyBanner" severity="info" closable @close="onDismissPasskeyBanner">
      <div class="flex items-center justify-between gap-4 flex-wrap">
        <span>Sign in faster next time — set up a passkey for your account.</span>
        <Button label="Set up a passkey" size="small" @click="onSetUpPasskey" />
      </div>
    </Message>

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
