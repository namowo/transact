<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { resetPassword } from '@/api/auth'
import { getErrorMessage } from '@/api/errors'

const route = useRoute()
const router = useRouter()

const token = (route.query.token as string | undefined) ?? ''
const newPassword = ref('')
const loading = ref(false)
const errorMessage = ref('')
const done = ref(false)

async function onSubmit() {
  if (!token) {
    errorMessage.value = 'This password reset link is missing its token.'
    return
  }
  loading.value = true
  errorMessage.value = ''
  try {
    await resetPassword(token, newPassword.value)
    done.value = true
  } catch (err) {
    errorMessage.value = getErrorMessage(
      err,
      'This password reset link is invalid or has expired.',
    )
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div v-if="done" class="flex flex-col gap-4 text-center">
    <i class="pi pi-check-circle text-4xl text-primary" />
    <p class="text-surface-700 dark:text-surface-200">
      Your password has been updated. You can now log in.
    </p>
    <Button label="Go to login" @click="router.push({ name: 'login' })" />
  </div>

  <form v-else class="flex flex-col gap-6" @submit.prevent="onSubmit">
    <div class="flex flex-col gap-1">
      <h1 class="text-3xl font-medium text-surface-900 dark:text-surface-0">Reset password</h1>
      <p class="text-sm text-surface-500 dark:text-surface-400">
        Enter a new password for your account
      </p>
    </div>
    <div class="flex flex-col gap-2">
      <label for="new-password" class="font-medium text-sm">New password</label>
      <Password
        input-id="new-password"
        v-model="newPassword"
        toggle-mask
        required
        fluid
        :disabled="!token"
      />
    </div>
    <Message v-if="errorMessage" severity="error" size="small">{{ errorMessage }}</Message>
    <Button type="submit" label="Reset password" :loading="loading" :disabled="!token" fluid />
    <p class="text-center text-sm">
      <RouterLink :to="{ name: 'login' }" class="text-primary no-underline hover:underline">
        Back to login
      </RouterLink>
    </p>
  </form>
</template>
