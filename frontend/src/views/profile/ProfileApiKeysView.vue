<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getErrorMessage } from '@/api/errors'
import * as apiKeysApi from '@/api/apiKeys'
import type { ApiKey } from '@/api/types'

const apiKeys = ref<ApiKey[]>([])
const apiKeysLoading = ref(false)
const apiKeysError = ref('')
const showAddApiKeyDialog = ref(false)
const newApiKeyName = ref('')
const newApiKeyExpiresAt = ref('')
const creatingApiKey = ref(false)
const createdApiKeyToken = ref('')
const showNewApiKeyDialog = ref(false)

async function loadApiKeys() {
  apiKeysLoading.value = true
  apiKeysError.value = ''
  try {
    apiKeys.value = await apiKeysApi.listApiKeys()
  } catch (err) {
    apiKeysError.value = getErrorMessage(err, 'Could not load your API keys.')
  } finally {
    apiKeysLoading.value = false
  }
}

function openAddApiKeyDialog() {
  newApiKeyName.value = ''
  newApiKeyExpiresAt.value = ''
  apiKeysError.value = ''
  showAddApiKeyDialog.value = true
}

async function onAddApiKey() {
  creatingApiKey.value = true
  apiKeysError.value = ''
  try {
    const created = await apiKeysApi.createApiKey({
      name: newApiKeyName.value.trim() || undefined,
      expires_at: newApiKeyExpiresAt.value
        ? new Date(newApiKeyExpiresAt.value).toISOString()
        : undefined,
    })
    showAddApiKeyDialog.value = false
    createdApiKeyToken.value = created.token
    showNewApiKeyDialog.value = true
    await loadApiKeys()
  } catch (err) {
    apiKeysError.value = getErrorMessage(err, 'Could not create this API key.')
  } finally {
    creatingApiKey.value = false
  }
}

async function onRevokeApiKey(apiKey: ApiKey) {
  const label = apiKey.name || `Key ${apiKey.prefix}…`
  if (!confirm(`Revoke ${label}? Anything using this key will stop working immediately.`)) return

  apiKeysError.value = ''
  try {
    await apiKeysApi.revokeApiKey(apiKey.id)
    await loadApiKeys()
  } catch (err) {
    apiKeysError.value = getErrorMessage(err, 'Could not revoke this API key.')
  }
}

async function copyApiKeyToken() {
  try {
    await navigator.clipboard.writeText(createdApiKeyToken.value)
  } catch {
    // Clipboard access can fail silently (e.g. insecure context); the token
    // stays visible in the dialog so the user can copy it manually.
  }
}

onMounted(loadApiKeys)
</script>

<template>
  <UCard>
    <template #header>
      <div class="flex items-center justify-between gap-4">
        <div>
          <h2 class="text-lg font-semibold text-highlighted">API keys</h2>
          <p class="text-sm text-muted">
            Use an API key to authenticate requests to the API instead of signing in.
          </p>
        </div>
        <UButton label="Create API key" icon="i-lucide-plus" size="sm" @click="openAddApiKeyDialog" />
      </div>
    </template>

    <div class="flex flex-col gap-4">
          <UAlert
            v-if="apiKeysError"
            color="error"
            variant="outline"
            :description="apiKeysError"
          />

          <div v-if="apiKeysLoading && apiKeys.length === 0" class="flex flex-col gap-2" aria-busy="true">
            <USkeleton v-for="n in 2" :key="n" class="h-14 w-full" />
          </div>

          <p v-else-if="apiKeys.length === 0" class="text-sm text-surface-500 dark:text-surface-400">
            No API keys yet.
          </p>

          <ul v-else class="flex flex-col gap-2 list-none p-0 m-0">
            <li
              v-for="apiKey in apiKeys"
              :key="apiKey.id"
              class="flex items-center justify-between gap-4 py-2 border-b border-surface-200 dark:border-surface-700 last:border-b-0"
            >
              <div class="flex flex-col">
                <span class="text-sm font-medium text-surface-900 dark:text-surface-0">
                  {{ apiKey.name || 'Unnamed key' }}
                  <code class="text-xs text-surface-500 dark:text-surface-400">{{ apiKey.prefix }}…</code>
                </span>
                <span class="text-xs text-surface-500 dark:text-surface-400">
                  Created {{ new Date(apiKey.created_at).toLocaleDateString() }}
                  <template v-if="apiKey.last_used_at">
                    · Last used {{ new Date(apiKey.last_used_at).toLocaleDateString() }}
                  </template>
                  <template v-if="apiKey.expires_at">
                    · Expires {{ new Date(apiKey.expires_at).toLocaleDateString() }}
                  </template>
                </span>
              </div>
              <UButton
                icon="i-lucide-trash-2"
                color="error"
                variant="ghost"
                aria-label="Revoke API key"
                @click="onRevokeApiKey(apiKey)"
              />
            </li>
          </ul>
    </div>

    <UModal
      v-model:open="showAddApiKeyDialog"
      title="Create API key"
      :ui="{ content: 'max-w-md', footer: 'justify-end' }"
    >
      <template #body>
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label for="api-key-name" class="font-medium text-sm">Name (optional)</label>
          <UInput
            id="api-key-name"
            v-model="newApiKeyName"
            placeholder="e.g. CI pipeline"
            class="w-full"
          />
        </div>
        <div class="flex flex-col gap-2">
          <label for="api-key-expires-at" class="font-medium text-sm">Expiration (optional)</label>
          <UInput
            id="api-key-expires-at"
            v-model="newApiKeyExpiresAt"
            type="date"
            class="w-full"
          />
        </div>
        <UAlert
          v-if="apiKeysError"
          color="error"
          variant="outline"
          :description="apiKeysError"
        />
      </div>
      </template>
      <template #footer>
        <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="showAddApiKeyDialog = false" />
        <UButton label="Create" icon="i-lucide-check" :loading="creatingApiKey" @click="onAddApiKey" />
      </template>
    </UModal>

    <UModal
      v-model:open="showNewApiKeyDialog"
      title="API key created"
      :ui="{ content: 'max-w-md', footer: 'justify-end' }"
    >
      <template #body>
      <div class="flex flex-col gap-4">
        <UAlert
          color="warning"
          variant="outline"
          description="Copy this key now. You won't be able to see it again."
        />
        <UInput :model-value="createdApiKeyToken" readonly class="w-full font-mono text-xs">
          <template #trailing>
            <UButton
              icon="i-lucide-copy"
              color="neutral"
              variant="link"
              size="sm"
              aria-label="Copy API key"
              @click="copyApiKeyToken"
            />
          </template>
        </UInput>
      </div>
      </template>
      <template #footer>
        <UButton label="Done" icon="i-lucide-check" @click="showNewApiKeyDialog = false" />
      </template>
    </UModal>
  </UCard>
</template>
