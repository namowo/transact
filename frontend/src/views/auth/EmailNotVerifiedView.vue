<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { resendVerification } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { getErrorMessage } from '@/api/errors'

const auth = useAuthStore()
const router = useRouter()

const resending = ref(false)
const resendMessage = ref('')
const checking = ref(false)

async function onResend() {
  if (!auth.user?.email) return
  resending.value = true
  resendMessage.value = ''
  try {
    await resendVerification(auth.user.email)
    resendMessage.value = 'Verification email resent. Please check your inbox.'
  } catch (err) {
    resendMessage.value = getErrorMessage(err, 'Could not resend the email. Please try again.')
  } finally {
    resending.value = false
  }
}

async function onLogout() {
  await auth.logout()
  router.push({ name: 'login' })
}

async function onCheckAgain() {
  checking.value = true
  resendMessage.value = ''
  try {
    await auth.fetchCurrentUser()
    if (auth.user?.is_verified) {
      router.push({ name: 'dashboard' })
    } else {
      resendMessage.value = 'Your email address is not confirmed yet.'
    }
  } finally {
    checking.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-4 text-center">
    <i class="pi pi-envelope text-4xl text-primary" />
    <h1 class="text-2xl font-medium text-surface-900 dark:text-surface-0">Confirm your email</h1>
    <p class="text-surface-700 dark:text-surface-200">
      Please confirm your email address to continue. We sent a confirmation link to
      <strong>{{ auth.user?.email }}</strong
      >.
    </p>

    <Message v-if="resendMessage" severity="info" size="small">{{ resendMessage }}</Message>

    <Button label="I've confirmed my email" :loading="checking" @click="onCheckAgain" />
    <Button label="Resend email" outlined :loading="resending" @click="onResend" />
    <Button label="Log out" text @click="onLogout" />
  </div>
</template>
