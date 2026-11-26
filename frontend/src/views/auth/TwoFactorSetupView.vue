<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { browserSupportsWebAuthn, startRegistration } from '@simplewebauthn/browser'
import { useAuthStore } from '@/stores/auth'
import { getErrorMessage } from '@/api/errors'
import * as webauthnApi from '@/api/webauthn'
import TotpSetupForm from '@/components/auth/TotpSetupForm.vue'
import RecoveryCodesList from '@/components/auth/RecoveryCodesList.vue'

// Shown after signing in while two-factor authentication is required and
// the user has no second factor yet.
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const step = ref<'choose' | 'totp' | 'recovery-codes'>('choose')
const recoveryCodes = ref<string[]>([])
const passkeyLoading = ref(false)
const error = ref('')
const passkeysSupported = browserSupportsWebAuthn()

async function finish() {
  await auth.fetchCurrentUser()
  router.push((route.query.redirect as string) || { name: 'dashboard' })
}

async function onAddPasskey() {
  error.value = ''
  passkeyLoading.value = true
  try {
    const options = await webauthnApi.getRegistrationOptions()
    const credential = await startRegistration({ optionsJSON: options })
    await webauthnApi.verifyRegistration(credential)
    await finish()
  } catch (err) {
    error.value = getErrorMessage(err, 'Could not register this passkey.')
  } finally {
    passkeyLoading.value = false
  }
}

function onTotpEnabled(codes: string[]) {
  recoveryCodes.value = codes
  step.value = 'recovery-codes'
}

async function onLogout() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex flex-col gap-1">
      <h1 class="text-3xl font-medium text-surface-900 dark:text-surface-0">
        <template v-if="step === 'recovery-codes'">You're all set</template>
        <template v-else>Secure your account</template>
      </h1>
      <p class="text-sm text-surface-500 dark:text-surface-400">
        <template v-if="step === 'choose'">
          This instance requires two-factor authentication. Choose how you want to confirm
          it's you when you sign in.
        </template>
        <template v-else-if="step === 'totp'">Set up your authenticator app.</template>
        <template v-else>Two-factor authentication is on.</template>
      </p>
    </div>

    <template v-if="step === 'choose'">
      <div class="flex flex-col gap-3">
        <UButton
          v-if="passkeysSupported"
          color="neutral"
          variant="outline"
          block
          :loading="passkeyLoading"
          class="justify-start p-4"
          @click="onAddPasskey"
        >
          <div class="flex items-start gap-3 text-left">
            <UIcon name="i-lucide-fingerprint" class="size-5 shrink-0 mt-0.5 text-primary" />
            <div class="flex flex-col gap-0.5">
              <span class="font-medium text-highlighted">Passkey</span>
              <span class="text-sm text-muted font-normal">
                Sign in with your fingerprint, face or device PIN instead of a password.
              </span>
            </div>
          </div>
        </UButton>
        <UButton
          color="neutral"
          variant="outline"
          block
          class="justify-start p-4"
          @click="step = 'totp'"
        >
          <div class="flex items-start gap-3 text-left">
            <UIcon name="i-lucide-smartphone" class="size-5 shrink-0 mt-0.5 text-primary" />
            <div class="flex flex-col gap-0.5">
              <span class="font-medium text-highlighted">Authenticator app</span>
              <span class="text-sm text-muted font-normal">
                Enter your password and a one-time code from an app on your phone.
              </span>
            </div>
          </div>
        </UButton>
      </div>
      <UAlert v-if="error" color="error" variant="outline" :description="error" />
    </template>

    <template v-else-if="step === 'totp'">
      <TotpSetupForm @enabled="onTotpEnabled" />
      <button
        type="button"
        class="self-start flex items-center gap-1 text-sm text-primary bg-transparent border-0 cursor-pointer p-0"
        @click="step = 'choose'"
      >
        <UIcon name="i-lucide-arrow-left" class="size-3" />
        Choose another method
      </button>
    </template>

    <template v-else>
      <RecoveryCodesList :codes="recoveryCodes" />
      <UButton label="Continue" icon="i-lucide-arrow-right" trailing block @click="finish" />
    </template>

    <p v-if="step !== 'recovery-codes'" class="text-center text-sm text-surface-600 dark:text-surface-300">
      Signed in as {{ auth.user?.email }}.
      <button
        type="button"
        class="text-primary bg-transparent border-0 cursor-pointer p-0 hover:underline"
        @click="onLogout"
      >
        Log out
      </button>
    </p>
  </div>
</template>
