<script setup lang="ts">
import { computed, ref } from 'vue'
import * as authApi from '@/api/auth'
import { getErrorMessage } from '@/api/errors'
import { useAuthStore } from '@/stores/auth'
import TotpSetupForm from '@/components/auth/TotpSetupForm.vue'
import TwoFactorCodeInput from '@/components/auth/TwoFactorCodeInput.vue'
import RecoveryCodesList from '@/components/auth/RecoveryCodesList.vue'

const auth = useAuthStore()

const totpEnabled = computed(() => !!auth.user?.totp_enabled)
const recoveryCodesRemaining = computed(() => auth.user?.recovery_codes_remaining ?? 0)

// Turning the authenticator app on: setup form, then the recovery codes.
const showSetup = ref(false)
const newRecoveryCodes = ref<string[]>([])

function openSetup() {
  newRecoveryCodes.value = []
  showSetup.value = true
}

async function onEnabled(codes: string[]) {
  newRecoveryCodes.value = codes
  await auth.fetchCurrentUser()
}

// Turning it off, or new recovery codes: both confirmed with a code.
const action = ref<'disable' | 'regenerate' | null>(null)
const password = ref('')
const code = ref('')
const busy = ref(false)
const actionError = ref('')

function openAction(kind: 'disable' | 'regenerate') {
  action.value = kind
  password.value = ''
  code.value = ''
  actionError.value = ''
  newRecoveryCodes.value = []
}

async function submitAction() {
  if (!code.value || (action.value === 'disable' && !password.value)) return
  busy.value = true
  actionError.value = ''
  try {
    if (action.value === 'disable') {
      await authApi.disableTotp(password.value, code.value)
      action.value = null
    } else {
      newRecoveryCodes.value = (await authApi.regenerateRecoveryCodes(code.value)).recovery_codes
    }
    await auth.fetchCurrentUser()
  } catch (err) {
    actionError.value = getErrorMessage(err, 'Could not confirm this code.')
    code.value = ''
  } finally {
    busy.value = false
  }
}

const actionOpen = computed({
  get: () => action.value !== null,
  set: (open: boolean) => {
    if (!open) action.value = null
  },
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <UCard>
      <template #header>
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="text-lg font-semibold text-highlighted">Two-factor authentication</h2>
            <p class="text-sm text-muted">
              Confirm it's you with a second step when you sign in with your password.
            </p>
          </div>
          <UBadge
            :label="totpEnabled ? 'On' : 'Off'"
            :color="totpEnabled ? 'success' : 'neutral'"
            variant="subtle"
          />
        </div>
      </template>

      <div class="flex flex-col gap-4">
        <UAlert
          v-if="auth.config.two_factor_required"
          color="info"
          variant="subtle"
          icon="i-lucide-info"
          description="This instance requires two-factor authentication: keep an authenticator app or a passkey set up."
        />

        <div class="flex items-center justify-between gap-4">
          <div class="flex items-start gap-3">
            <UIcon name="i-lucide-smartphone" class="size-5 shrink-0 mt-0.5 text-muted" />
            <div class="flex flex-col">
              <span class="text-sm font-medium text-highlighted">Authenticator app</span>
              <span class="text-sm text-muted">
                <template v-if="totpEnabled">
                  On · {{ recoveryCodesRemaining }} recovery
                  {{ recoveryCodesRemaining === 1 ? 'code' : 'codes' }} left
                </template>
                <template v-else>One-time codes from an app on your phone.</template>
              </span>
            </div>
          </div>
          <div class="flex gap-2 shrink-0">
            <template v-if="totpEnabled">
              <UButton
                label="New recovery codes"
                color="neutral"
                variant="outline"
                size="sm"
                @click="openAction('regenerate')"
              />
              <UButton
                label="Turn off"
                color="error"
                variant="ghost"
                size="sm"
                @click="openAction('disable')"
              />
            </template>
            <UButton v-else label="Set up" icon="i-lucide-plus" size="sm" @click="openSetup" />
          </div>
        </div>

        <USeparator />

        <div class="flex items-center justify-between gap-4">
          <div class="flex items-start gap-3">
            <UIcon name="i-lucide-fingerprint" class="size-5 shrink-0 mt-0.5 text-muted" />
            <div class="flex flex-col">
              <span class="text-sm font-medium text-highlighted">Passkeys</span>
              <span class="text-sm text-muted">
                A passkey counts as both factors: your device, and the fingerprint, face or PIN
                that unlocks it.
              </span>
            </div>
          </div>
          <UButton
            label="Manage"
            color="neutral"
            variant="outline"
            size="sm"
            class="shrink-0"
            :to="{ name: 'profile-passkeys' }"
          />
        </div>
      </div>
    </UCard>

    <UModal
      v-model:open="showSetup"
      title="Set up the authenticator app"
      :ui="{ content: 'max-w-md', footer: 'justify-end' }"
    >
      <template #body>
        <RecoveryCodesList v-if="newRecoveryCodes.length" :codes="newRecoveryCodes" />
        <TotpSetupForm v-else @enabled="onEnabled" />
      </template>
      <template v-if="newRecoveryCodes.length" #footer>
        <UButton label="Done" icon="i-lucide-check" @click="showSetup = false" />
      </template>
    </UModal>

    <UModal
      v-model:open="actionOpen"
      :title="action === 'disable' ? 'Turn off the authenticator app' : 'New recovery codes'"
      :ui="{ content: 'max-w-md', footer: 'justify-end' }"
    >
      <template #body>
        <RecoveryCodesList v-if="newRecoveryCodes.length" :codes="newRecoveryCodes" />
        <form v-else class="flex flex-col gap-4" @submit.prevent="submitAction">
          <p class="m-0 text-sm text-muted">
            <template v-if="action === 'disable'">
              You'll sign in with your password alone.
            </template>
            <template v-else>Your current recovery codes will stop working.</template>
          </p>
          <div v-if="action === 'disable'" class="flex flex-col gap-2">
            <label for="two-factor-password" class="font-medium text-sm">Current password</label>
            <UInput
              id="two-factor-password"
              v-model="password"
              type="password"
              autocomplete="current-password"
              class="w-full"
            />
          </div>
          <TwoFactorCodeInput
            v-model="code"
            allow-recovery-code
            :autofocus="action !== 'disable'"
            :disabled="busy"
          />
          <UAlert v-if="actionError" color="error" variant="outline" :description="actionError" />
          <!-- Submit on Enter. -->
          <button type="submit" hidden />
        </form>
      </template>
      <template #footer>
        <template v-if="newRecoveryCodes.length">
          <UButton label="Done" icon="i-lucide-check" @click="action = null" />
        </template>
        <template v-else>
          <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="action = null" />
          <UButton
            :label="action === 'disable' ? 'Turn off' : 'Create new codes'"
            :color="action === 'disable' ? 'error' : 'primary'"
            :loading="busy"
            :disabled="!code || (action === 'disable' && !password)"
            @click="submitAction"
          />
        </template>
      </template>
    </UModal>

    <p class="text-sm text-muted m-0">
      Lost your authenticator app and recovery codes? Ask an administrator to reset your
      two-factor authentication.
    </p>
  </div>
</template>
