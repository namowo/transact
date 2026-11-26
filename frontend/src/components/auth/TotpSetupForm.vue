<script setup lang="ts">
import { onMounted, ref } from 'vue'
import QRCode from 'qrcode'
import * as authApi from '@/api/auth'
import { getErrorMessage } from '@/api/errors'
import TwoFactorCodeInput from '@/components/auth/TwoFactorCodeInput.vue'

// Sets up the authenticator app: scan the QR code, confirm a code. Emits
// the recovery codes once it's on.
const emit = defineEmits<{ enabled: [recoveryCodes: string[]] }>()

const loading = ref(true)
const confirming = ref(false)
const error = ref('')
const secret = ref('')
const qrDataUrl = ref('')
const code = ref('')
const showSecret = ref(false)

async function start() {
  loading.value = true
  error.value = ''
  try {
    const setup = await authApi.startTotpSetup()
    secret.value = setup.secret
    qrDataUrl.value = await QRCode.toDataURL(setup.provisioning_uri, { margin: 1, width: 192 })
  } catch (err) {
    error.value = getErrorMessage(err, 'Could not start setting up the authenticator app.')
  } finally {
    loading.value = false
  }
}

async function confirm(value = code.value) {
  if (value.length !== 6 || confirming.value) return
  confirming.value = true
  error.value = ''
  try {
    const { recovery_codes } = await authApi.enableTotp(value)
    emit('enabled', recovery_codes)
  } catch (err) {
    error.value = getErrorMessage(err, 'Could not confirm this code.')
    code.value = ''
  } finally {
    confirming.value = false
  }
}

// Groups of four, easier to type.
function formatSecret(value: string) {
  return value.match(/.{1,4}/g)?.join(' ') ?? value
}

onMounted(start)
</script>

<template>
  <form class="flex flex-col gap-4" @submit.prevent="confirm()">
    <div v-if="loading" class="flex flex-col gap-4" aria-busy="true">
      <USkeleton class="h-4 w-3/4" />
      <USkeleton class="size-40 self-center" />
      <USkeleton class="h-4 w-1/2" />
      <USkeleton class="h-10 w-full" />
    </div>

    <template v-else-if="secret">
      <ol class="flex flex-col gap-4 m-0 ps-5 text-sm">
        <li>
          <p class="m-0 mb-3">
            Scan this QR code with an authenticator app, such as 1Password, Google
            Authenticator or Microsoft Authenticator.
          </p>
          <div class="flex flex-col items-start gap-2">
            <img
              :src="qrDataUrl"
              alt="QR code for your authenticator app"
              class="size-48 rounded-md bg-white p-2"
            />
            <button
              type="button"
              class="flex items-center gap-1 text-sm text-primary bg-transparent border-0 cursor-pointer p-0"
              @click="showSecret = !showSecret"
            >
              <UIcon name="i-lucide-keyboard" class="size-3" />
              Can't scan it? Enter the key by hand
            </button>
            <code
              v-if="showSecret"
              class="px-2 py-1 rounded bg-elevated font-mono text-sm break-all select-all"
              >{{ formatSecret(secret) }}</code
            >
          </div>
        </li>
        <li>
          <p class="m-0 mb-3">Enter the six-digit code the app shows.</p>
          <TwoFactorCodeInput v-model="code" :disabled="confirming" @complete="confirm" />
        </li>
      </ol>
    </template>

    <UAlert v-if="error" color="error" variant="outline" :description="error" />

    <div v-if="!loading" class="flex gap-2">
      <UButton
        v-if="secret"
        type="submit"
        label="Turn on"
        icon="i-lucide-check"
        :loading="confirming"
        :disabled="code.length !== 6"
      />
      <UButton v-else label="Try again" icon="i-lucide-rotate-ccw" @click="start" />
    </div>
  </form>
</template>
