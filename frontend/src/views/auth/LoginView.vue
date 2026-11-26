<script setup lang="ts">
import { computed, ref } from 'vue'
import axios from 'axios'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { startAuthentication } from '@simplewebauthn/browser'
import { useAuthStore } from '@/stores/auth'
import { getErrorMessage } from '@/api/errors'
import * as webauthnApi from '@/api/webauthn'
import type { TwoFactorChallenge } from '@/api/types'
import TwoFactorCodeInput from '@/components/auth/TwoFactorCodeInput.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const loading = ref(false)
const passkeyLoading = ref(false)
const errorMessage = ref('')
const loginFailed = ref(false)
const step = ref<'email' | 'password' | 'two-factor'>('email')
// After a correct password, when a second factor is needed.
const challenge = ref<TwoFactorChallenge | null>(null)
const code = ref('')
const codeLoading = ref(false)
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

function goToRedirect() {
  const redirect = (route.query.redirect as string) || { name: 'dashboard' }
  router.push(redirect)
}

function onBack() {
  step.value = 'email'
  challenge.value = null
  code.value = ''
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
    const result = await auth.login(values.email.trim(), values.password)
    if (result) {
      challenge.value = result
      code.value = ''
      step.value = 'two-factor'
      return
    }
    goToRedirect()
  } catch (err) {
    errorMessage.value = getErrorMessage(err, 'Could not log in. Please check your credentials.')
    loginFailed.value = true
  } finally {
    loading.value = false
  }
})

async function onSubmitCode(value = code.value) {
  const loginToken = challenge.value?.login_token
  if (!loginToken || !value || codeLoading.value) return
  errorMessage.value = ''
  codeLoading.value = true
  try {
    await auth.loginTwoFactor(loginToken, value)
    goToRedirect()
  } catch (err) {
    code.value = ''
    if (axios.isAxiosError(err) && err.response?.status === 401) {
      // The sign-in took too long: start over.
      onBack()
    }
    errorMessage.value = getErrorMessage(err, 'Could not verify this code.')
  } finally {
    codeLoading.value = false
  }
}

async function onSubmitStep() {
  if (step.value === 'two-factor') {
    await onSubmitCode()
    return
  }
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
    goToRedirect()
  } catch (err) {
    errorMessage.value = getErrorMessage(err, 'Could not log in with a passkey.')
    loginFailed.value = true
  } finally {
    passkeyLoading.value = false
  }
}
const canUseTotp = computed(() => !!challenge.value?.methods.includes('totp'))
const canUsePasskey = computed(() => !!challenge.value?.methods.includes('passkey'))
</script>

<template>
  <form class="flex flex-col gap-6" @submit.prevent="onSubmitStep">
    <div class="flex flex-col gap-1">
      <h1 class="text-3xl font-medium text-surface-900 dark:text-surface-0">Login</h1>
      <p class="text-sm text-surface-500 dark:text-surface-400">
        <template v-if="step === 'email'"
          >Enter your email below to log in to your account</template
        >
        <template v-else-if="step === 'password'">
          Enter your password for
          <strong class="text-surface-700 dark:text-surface-200">{{ email }}</strong>
        </template>
        <template v-else-if="canUseTotp">
          Enter the code from your authenticator app to finish signing in.
        </template>
        <template v-else>
          Your account signs in with a passkey. Use it to finish signing in.
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

    <div v-else-if="step === 'two-factor'" class="flex flex-col gap-3">
      <TwoFactorCodeInput
        v-if="canUseTotp"
        v-model="code"
        allow-recovery-code
        :disabled="codeLoading"
        @complete="onSubmitCode"
      />
      <UButton
        v-if="canUsePasskey"
        type="button"
        :label="canUseTotp ? 'Use a passkey instead' : 'Continue with passkey'"
        icon="i-lucide-key"
        :color="canUseTotp ? 'neutral' : 'primary'"
        :variant="canUseTotp ? 'link' : 'solid'"
        :block="!canUseTotp"
        :loading="passkeyLoading"
        :class="canUseTotp ? 'self-start p-0' : ''"
        @click="onUsePasskey(true)"
      />
      <button
        type="button"
        class="self-start flex items-center gap-1 text-sm text-primary bg-transparent border-0 cursor-pointer p-0"
        @click="onBack"
      >
        <UIcon name="i-lucide-arrow-left" class="size-3" />
        Start over
      </button>
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
        <UAlert
          v-if="errors.password"
          color="error"
          variant="subtle"
          :description="errors.password"
        />
      </div>
      <button
        type="button"
        class="self-start flex items-center gap-1 text-sm text-primary bg-transparent border-0 cursor-pointer p-0 disabled:opacity-50"
        :disabled="passkeyLoading"
        @click="onUsePasskey(true)"
      >
        <UIcon name="i-lucide-key-round" class="size-3" />
        {{ passkeyLoading ? 'Waiting for passkey…' : 'Use a passkey instead' }}
      </button>
      <button
        type="button"
        class="self-start flex items-center gap-1 text-sm text-primary bg-transparent border-0 cursor-pointer p-0"
        @click="onBack"
      >
        <UIcon name="i-lucide-arrow-left" class="size-3" />
        Use a different email
      </button>
    </div>

    <UAlert v-if="errorMessage" color="error" variant="outline" :description="errorMessage" />

    <p
      v-if="loginFailed && auth.config.registration_enabled"
      class="text-sm text-surface-600 dark:text-surface-300 -mt-2"
    >
      New here?
      <RouterLink
        :to="{ name: 'register', query: { email } }"
        class="text-primary no-underline hover:underline"
      >
        Create an account
      </RouterLink>
      instead.
    </p>

    <UButton
      v-if="step !== 'two-factor' || canUseTotp"
      type="submit"
      :label="step === 'email' ? 'Continue' : 'Log in'"
      :loading="loading || codeLoading"
      :disabled="step === 'two-factor' && !code"
      block
    />

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

    <p
      v-if="auth.config.registration_enabled && step !== 'two-factor'"
      class="text-center text-sm text-surface-600 dark:text-surface-300 mt-2"
    >
      Don't have an account?
      <RouterLink
        :to="{ name: 'register', query: { email } }"
        class="text-primary no-underline hover:underline"
      >
        Sign Up
      </RouterLink>
    </p>
  </form>
</template>
