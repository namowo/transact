<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { useAuthStore } from '@/stores/auth'
import { getErrorMessage } from '@/api/errors'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')
const loginFailed = ref(false)
const step = ref<'email' | 'password'>('email')

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function onBack() {
  step.value = 'email'
  password.value = ''
  errorMessage.value = ''
  loginFailed.value = false
}

async function onSubmit() {
  errorMessage.value = ''
  loginFailed.value = false

  if (step.value === 'email') {
    if (!emailPattern.test(email.value.trim())) {
      errorMessage.value = 'Please enter a valid email address.'
      return
    }
    step.value = 'password'
    return
  }

  loading.value = true
  try {
    await auth.login(email.value, password.value)
    const redirect = (route.query.redirect as string) || { name: 'dashboard' }
    router.push(redirect)
  } catch (err) {
    errorMessage.value = getErrorMessage(err, 'Could not log in. Please check your credentials.')
    loginFailed.value = true
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <form class="flex flex-col gap-6" @submit.prevent="onSubmit">
    <div class="flex flex-col gap-1">
      <h1 class="text-3xl font-medium text-surface-900 dark:text-surface-0">Login</h1>
      <p class="text-sm text-surface-500 dark:text-surface-400">
        <template v-if="step === 'email'">Enter your email below to log in to your account</template>
        <template v-else>
          Enter your password for
          <strong class="text-surface-700 dark:text-surface-200">{{ email }}</strong>
        </template>
      </p>
    </div>

    <div v-if="step === 'email'" class="flex flex-col gap-2">
      <label for="email" class="font-medium text-sm">Email</label>
      <InputText id="email" v-model="email" type="email" required autofocus fluid />
    </div>

    <div v-else class="flex flex-col gap-3">
      <div class="flex flex-col gap-2">
        <div class="flex items-center justify-between">
          <label for="password" class="font-medium text-sm">Password</label>
          <RouterLink
            :to="{ name: 'forgot-password' }"
            class="text-sm text-primary no-underline hover:underline"
          >
            Forgot password?
          </RouterLink>
        </div>
        <Password
          input-id="password"
          v-model="password"
          :feedback="false"
          toggle-mask
          required
          autofocus
          fluid
        />
      </div>
      <button
        type="button"
        class="self-start flex items-center gap-1 text-sm text-primary bg-transparent border-0 cursor-pointer p-0"
        @click="onBack"
      >
        <i class="pi pi-arrow-left text-xs" />
        Use a different email
      </button>
    </div>

    <Message v-if="errorMessage" severity="error" size="small">{{ errorMessage }}</Message>

    <p v-if="loginFailed" class="text-sm text-surface-600 dark:text-surface-300 -mt-2">
      New here?
      <RouterLink
        :to="{ name: 'register', query: { email } }"
        class="text-primary no-underline hover:underline"
      >
        Create an account
      </RouterLink>
      instead.
    </p>

    <Button type="submit" :label="step === 'email' ? 'Continue' : 'Log in'" :loading="loading" fluid />

    <p class="text-center text-sm text-surface-600 dark:text-surface-300 mt-2">
      Don't have an account?
      <RouterLink :to="{ name: 'register', query: { email } }" class="text-primary no-underline hover:underline">
        Sign Up
      </RouterLink>
    </p>
  </form>
</template>
