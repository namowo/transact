<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
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
    <UAlert
      v-if="showPasskeyBanner"
      color="info"
      variant="outline"
      description="Sign in faster next time — set up a passkey for your account."
      orientation="horizontal"
      close
      @update:open="onDismissPasskeyBanner"
    >
      <template #actions>
        <UButton label="Set up a passkey" size="sm" @click="onSetUpPasskey" />
      </template>
    </UAlert>

    <div>
      <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">
        Welcome, {{ auth.user?.first_name }}
      </h1>
      <p class="text-surface-600 dark:text-surface-300">
        {{ auth.user?.laboratory?.laboratory_name }}
      </p>
    </div>

    <UCard>
      <template #header>Your account</template>
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
    </UCard>
  </div>
</template>
