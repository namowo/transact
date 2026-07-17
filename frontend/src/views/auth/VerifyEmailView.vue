<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import ProgressSpinner from 'primevue/progressspinner'
import { verifyEmail } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { getErrorMessage } from '@/api/errors'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const status = ref<'loading' | 'success' | 'error'>('loading')
const errorMessage = ref('')

onMounted(async () => {
  const token = route.query.token as string | undefined
  if (!token) {
    status.value = 'error'
    errorMessage.value = 'This verification link is missing its token.'
    return
  }
  try {
    await verifyEmail(token)
    if (auth.isAuthenticated) {
      await auth.fetchCurrentUser()
    }
    status.value = 'success'
  } catch (err) {
    status.value = 'error'
    errorMessage.value = getErrorMessage(
      err,
      'This verification link is invalid or has expired.',
    )
  }
})
</script>

<template>
  <div class="flex flex-col items-center gap-4 text-center">
    <ProgressSpinner v-if="status === 'loading'" style="width: 3rem; height: 3rem" />

    <template v-else-if="status === 'success'">
      <i class="pi pi-check-circle text-4xl text-primary" />
      <p class="text-surface-700 dark:text-surface-200">
        Your email address has been confirmed.
        {{ auth.isAuthenticated ? '' : 'You can now log in.' }}
      </p>
      <Button
        v-if="auth.isAuthenticated"
        label="Continue"
        @click="router.push({ name: 'dashboard' })"
      />
      <Button v-else label="Go to login" @click="router.push({ name: 'login' })" />
    </template>

    <template v-else>
      <i class="pi pi-times-circle text-4xl text-red-500" />
      <p class="text-surface-700 dark:text-surface-200">{{ errorMessage }}</p>
      <RouterLink :to="{ name: 'login' }" class="text-primary no-underline hover:underline">
        Back to login
      </RouterLink>
    </template>
  </div>
</template>
