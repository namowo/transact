<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { startRegistration } from '@simplewebauthn/browser'
import { getErrorMessage } from '@/api/errors'
import * as webauthnApi from '@/api/webauthn'
import type { WebAuthnCredential } from '@/api/types'

const credentials = ref<WebAuthnCredential[]>([])
const credentialsLoading = ref(false)
const credentialsError = ref('')
const showAddPasskeyDialog = ref(false)
const newDeviceName = ref('')
const addingPasskey = ref(false)

async function loadCredentials() {
  credentialsLoading.value = true
  credentialsError.value = ''
  try {
    credentials.value = await webauthnApi.listCredentials()
  } catch (err) {
    credentialsError.value = getErrorMessage(err, 'Could not load your passkeys.')
  } finally {
    credentialsLoading.value = false
  }
}

function openAddPasskeyDialog() {
  newDeviceName.value = ''
  credentialsError.value = ''
  showAddPasskeyDialog.value = true
}

async function onAddPasskey() {
  addingPasskey.value = true
  credentialsError.value = ''
  try {
    const options = await webauthnApi.getRegistrationOptions()
    const credential = await startRegistration({ optionsJSON: options })
    await webauthnApi.verifyRegistration(credential, newDeviceName.value.trim() || undefined)
    showAddPasskeyDialog.value = false
    await loadCredentials()
  } catch (err) {
    credentialsError.value = getErrorMessage(err, 'Could not register this passkey.')
  } finally {
    addingPasskey.value = false
  }
}

async function onDeletePasskey(credential: WebAuthnCredential) {
  const label = credential.device_name || 'this passkey'
  if (!confirm(`Remove ${label}? You will no longer be able to use it to log in.`)) return

  credentialsError.value = ''
  try {
    await webauthnApi.deleteCredential(credential.id)
    await loadCredentials()
  } catch (err) {
    credentialsError.value = getErrorMessage(err, 'Could not remove this passkey.')
  }
}

onMounted(loadCredentials)
</script>

<template>
  <UCard>
    <template #header>
      <div class="flex items-center justify-between gap-4">
        <div>
          <h2 class="text-lg font-semibold text-highlighted">Passkeys</h2>
          <p class="text-sm text-muted">
            Use a passkey to sign in without a password, on this device or others.
          </p>
        </div>
        <UButton label="Add a passkey" icon="i-lucide-plus" size="sm" @click="openAddPasskeyDialog" />
      </div>
    </template>

    <div class="flex flex-col gap-4">
          <UAlert
            v-if="credentialsError"
            color="error"
            variant="outline"
            :description="credentialsError"
          />

          <div v-if="credentialsLoading && credentials.length === 0" class="flex flex-col gap-2" aria-busy="true">
            <USkeleton v-for="n in 2" :key="n" class="h-14 w-full" />
          </div>

          <p v-else-if="credentials.length === 0" class="text-sm text-surface-500 dark:text-surface-400">
            No passkeys registered yet.
          </p>

          <ul v-else class="flex flex-col gap-2 list-none p-0 m-0">
            <li
              v-for="credential in credentials"
              :key="credential.id"
              class="flex items-center justify-between gap-4 py-2 border-b border-surface-200 dark:border-surface-700 last:border-b-0"
            >
              <div class="flex flex-col">
                <span class="text-sm font-medium text-surface-900 dark:text-surface-0">
                  {{ credential.device_name || 'Unnamed passkey' }}
                </span>
                <span class="text-xs text-surface-500 dark:text-surface-400">
                  Added {{ new Date(credential.created_at).toLocaleDateString() }}
                  <template v-if="credential.last_used_at">
                    · Last used {{ new Date(credential.last_used_at).toLocaleDateString() }}
                  </template>
                </span>
              </div>
              <UButton
                icon="i-lucide-trash-2"
                color="error"
                variant="ghost"
                aria-label="Delete passkey"
                @click="onDeletePasskey(credential)"
              />
            </li>
          </ul>
    </div>

    <UModal
      v-model:open="showAddPasskeyDialog"
      title="Add a passkey"
      :ui="{ content: 'max-w-md', footer: 'justify-end' }"
    >
      <template #body>
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label for="device-name" class="font-medium text-sm">Device name (optional)</label>
          <UInput
            id="device-name"
            v-model="newDeviceName"
            placeholder="e.g. MacBook Pro"
            class="w-full"
          />
        </div>
        <UAlert
          v-if="credentialsError"
          color="error"
          variant="outline"
          :description="credentialsError"
        />
      </div>
      </template>
      <template #footer>
        <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="showAddPasskeyDialog = false" />
        <UButton label="Continue" icon="i-lucide-check" :loading="addingPasskey" @click="onAddPasskey" />
      </template>
    </UModal>
  </UCard>
</template>
