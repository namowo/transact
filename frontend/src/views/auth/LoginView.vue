<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { startAuthentication } from '@simplewebauthn/browser'
import { useAuthStore } from '@/stores/auth'
import { getErrorMessage } from '@/api/errors'
import * as webauthnApi from '@/api/webauthn'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const loading = ref(false)
const passkeyLoading = ref(false)
const errorMessage = ref('')
const loginFailed = ref(false)
const step = ref<'email' | 'password'>('email')
const showPassword = ref(false)

const schema = yup.object({
  email: yup.string().trim().email('Please enter a valid email address.').required(),
  password: yup.string().when([], {
    is: () => step.value === 'password',
    then: (s) => s.required('Password is required.'),
    otherwise: (s) => s.defined(),
  }),
})

const { defineField, errors, handleSubmit, validateField } = useForm({
  validationSchema: schema,
  initialValues: { email: '', password: '' },
})

const [email] = defineField('email')
const [password] = defineField('password')

function onBack() {
  step.value = 'email'
  password.value = ''
  errorMessage.value = ''
  loginFailed.value = false
}

const onSubmit = handleSubmit(async (values) => {
  errorMessage.value = ''
  loginFailed.value = false

  if (step.value === 'email') {
    step.value = 'password'
    return
  }

  loading.value = true
  try {
    await auth.login(values.email.trim(), values.password)
    const redirect = (route.query.redirect as string) || { name: 'dashboard' }
    router.push(redirect)
  } catch (err) {
    errorMessage.value = getErrorMessage(err, 'Could not log in. Please check your credentials.')
    loginFailed.value = true
  } finally {
    loading.value = false
  }
})

async function onSubmitStep() {
  if (step.value === 'email') {
    const result = await validateField('email')
    if (!result.valid) return
  }
  await onSubmit()
}

async function onUsePasskey(useEmail: boolean) {
  errorMessage.value = ''
  loginFailed.value = false
  passkeyLoading.value = true
  try {
    const trimmedEmail = email.value.trim() || undefined
    const options = await webauthnApi.getLoginOptions(useEmail ? trimmedEmail : undefined)
    const credential = await startAuthentication({ optionsJSON: options })
    await webauthnApi.verifyLogin(useEmail ? trimmedEmail : undefined, credential)
    await auth.fetchCurrentUser()
    const redirect = (route.query.redirect as string) || { name: 'dashboard' }
    router.push(redirect)
  } catch (err) {
    errorMessage.value = getErrorMessage(err, 'Could not log in with a passkey.')
    loginFailed.value = true
  } finally {
    passkeyLoading.value = false
  }
}
</script>

<template>
  <form class="flex flex-col gap-6" @submit.prevent="onSubmitStep">
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
      <UInput
        id="email"
        v-model="email"
        type="email"
        :color="errors.email ? 'error' : undefined"
        autofocus
        class="w-full"
      />
      <UAlert v-if="errors.email" color="error" variant="subtle" :description="errors.email" />
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
        <UInput
          id="password"
          v-model="password"
          :type="showPassword ? 'text' : 'password'"
          :color="errors.password ? 'error' : undefined"
          autofocus
          class="w-full"
          :ui="{ trailing: 'pe-1' }"
        >
          <template #trailing>
            <UButton
              color="neutral"
              variant="link"
              size="sm"
              :icon="showPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'"
              :aria-label="showPassword ? 'Hide password' : 'Show password'"
              :aria-pressed="showPassword"
              @click="showPassword = !showPassword"
            />
          </template>
        </UInput>
        <UAlert v-if="errors.password" color="error" variant="subtle" :description="errors.password" />
      </div>
      <button
        type="button"
        class="self-start flex items-center gap-1 text-sm text-primary bg-transparent border-0 cursor-pointer p-0 disabled:opacity-50"
        :disabled="passkeyLoading"
        @click="onUsePasskey(true)"
      >
        <i class="pi pi-key text-xs" />
        {{ passkeyLoading ? 'Waiting for passkey…' : 'Use a passkey instead' }}
      </button>
      <button
        type="button"
        class="self-start flex items-center gap-1 text-sm text-primary bg-transparent border-0 cursor-pointer p-0"
        @click="onBack"
      >
        <i class="pi pi-arrow-left text-xs" />
        Use a different email
      </button>
    </div>

    <UAlert v-if="errorMessage" color="error" variant="outline" :description="errorMessage" />

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

    <UButton type="submit" :label="step === 'email' ? 'Continue' : 'Log in'" :loading="loading" block />

    <template v-if="step === 'email'">
      <USeparator label="or" class="my-0!" />
      <UButton
        type="button"
        label="Log in with passkey"
        icon="i-lucide-key"
        color="neutral"
        :loading="passkeyLoading"
        block
        @click="onUsePasskey(false)"
      />
    </template>

    <p class="text-center text-sm text-surface-600 dark:text-surface-300 mt-2">
      Don't have an account?
      <RouterLink :to="{ name: 'register', query: { email } }" class="text-primary no-underline hover:underline">
        Sign Up
      </RouterLink>
    </p>
  </form>
</template>
