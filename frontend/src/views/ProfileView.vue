<script setup lang="ts">
import { onMounted, ref, watchEffect } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { startRegistration } from '@simplewebauthn/browser'
import PasswordField from '@/components/auth/PasswordField.vue'
import { useAuthStore } from '@/stores/auth'
import { getErrorMessage } from '@/api/errors'
import * as webauthnApi from '@/api/webauthn'
import * as apiKeysApi from '@/api/apiKeys'
import type { ApiKey, WebAuthnCredential } from '@/api/types'

const auth = useAuthStore()

const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

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

const schema = yup.object({
  firstName: yup.string().trim().required('First name is required.'),
  lastName: yup.string().trim().required('Last name is required.'),
})

const { defineField, errors, handleSubmit, resetForm } = useForm({
  validationSchema: schema,
  initialValues: { firstName: '', lastName: '' },
})

const [firstName] = defineField('firstName')
const [lastName] = defineField('lastName')

watchEffect(() => {
  resetForm({
    values: {
      firstName: auth.user?.first_name ?? '',
      lastName: auth.user?.last_name ?? '',
    },
  })
})

const onSubmit = handleSubmit(async (values) => {
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await auth.updateProfile({
      first_name: values.firstName.trim(),
      last_name: values.lastName.trim(),
    })
    successMessage.value = 'Profile updated.'
  } catch (err) {
    errorMessage.value = getErrorMessage(err, 'Could not update your profile. Please try again.')
  } finally {
    loading.value = false
  }
})

const emailSchema = yup.object({
  currentPassword: yup.string().required('Current password is required.'),
  newEmail: yup.string().trim().email('Enter a valid email address.').required('New email is required.'),
})

const emailLoading = ref(false)
const emailErrorMessage = ref('')
const emailSuccessMessage = ref('')

const {
  defineField: defineEmailField,
  errors: emailErrors,
  handleSubmit: handleEmailSubmit,
  resetForm: resetEmailForm,
} = useForm({
  validationSchema: emailSchema,
  initialValues: { currentPassword: '', newEmail: '' },
})

const [emailCurrentPassword] = defineEmailField('currentPassword')
const [newEmail] = defineEmailField('newEmail')

const onEmailSubmit = handleEmailSubmit(async (values) => {
  emailLoading.value = true
  emailErrorMessage.value = ''
  emailSuccessMessage.value = ''
  try {
    await auth.changeMyEmail({
      current_password: values.currentPassword,
      new_email: values.newEmail.trim(),
    })
    emailSuccessMessage.value = 'Email address updated.'
    resetEmailForm({ values: { currentPassword: '', newEmail: '' } })
  } catch (err) {
    emailErrorMessage.value = getErrorMessage(err, 'Could not update your email address. Please try again.')
  } finally {
    emailLoading.value = false
  }
})

const passwordSchema = yup.object({
  currentPassword: yup.string().required('Current password is required.'),
  newPassword: yup
    .string()
    .required('New password is required.')
    .min(8, 'Password must be at least 8 characters.')
    .matches(/\d/, 'Password must contain a number.')
    .matches(/[A-Z]/, 'Password must contain an uppercase letter.')
    .matches(/[^a-zA-Z0-9]/, 'Password must contain a special character.'),
  confirmPassword: yup
    .string()
    .required('Please confirm your new password.')
    .oneOf([yup.ref('newPassword')], 'Passwords do not match.'),
})

const passwordLoading = ref(false)
const passwordErrorMessage = ref('')
const passwordSuccessMessage = ref('')
const showEmailCurrentPassword = ref(false)
const showPasswordCurrentPassword = ref(false)
const showConfirmPassword = ref(false)

const {
  defineField: definePasswordField,
  errors: passwordErrors,
  handleSubmit: handlePasswordSubmit,
  resetForm: resetPasswordForm,
} = useForm({
  validationSchema: passwordSchema,
  initialValues: { currentPassword: '', newPassword: '', confirmPassword: '' },
})

const [passwordCurrentPassword] = definePasswordField('currentPassword')
const [newPassword] = definePasswordField('newPassword')
const [confirmPassword] = definePasswordField('confirmPassword')

const onPasswordSubmit = handlePasswordSubmit(async (values) => {
  passwordLoading.value = true
  passwordErrorMessage.value = ''
  passwordSuccessMessage.value = ''
  try {
    await auth.changeMyPassword({
      current_password: values.currentPassword,
      new_password: values.newPassword,
    })
    passwordSuccessMessage.value = 'Password updated.'
    resetPasswordForm({ values: { currentPassword: '', newPassword: '', confirmPassword: '' } })
  } catch (err) {
    passwordErrorMessage.value = getErrorMessage(err, 'Could not update your password. Please try again.')
  } finally {
    passwordLoading.value = false
  }
})
</script>

<template>
  <div class="flex flex-col gap-6 max-w-lg">
    <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Edit profile</h1>

    <UCard>
        <form class="flex flex-col gap-4" @submit.prevent="onSubmit">
          <div class="flex flex-col sm:flex-row gap-4">
            <div class="flex flex-col gap-2 flex-1">
              <label for="first-name" class="font-medium text-sm">First name</label>
              <UInput
                id="first-name"
                v-model="firstName"
                :color="errors.firstName ? 'error' : undefined"
                class="w-full"
              />
              <UAlert
                v-if="errors.firstName"
                color="error"
                variant="subtle"
                :description="errors.firstName"
              />
            </div>
            <div class="flex flex-col gap-2 flex-1">
              <label for="last-name" class="font-medium text-sm">Last name</label>
              <UInput
                id="last-name"
                v-model="lastName"
                :color="errors.lastName ? 'error' : undefined"
                class="w-full"
              />
              <UAlert
                v-if="errors.lastName"
                color="error"
                variant="subtle"
                :description="errors.lastName"
              />
            </div>
          </div>

          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Laboratory</label>
            <UInput
              :model-value="auth.user?.laboratory?.laboratory_name"
              disabled
              class="w-full"
            />
          </div>

          <UAlert v-if="errorMessage" color="error" variant="outline" :description="errorMessage" />
          <UAlert
            v-if="successMessage"
            color="success"
            variant="outline"
            :description="successMessage"
          />

          <UButton type="submit" label="Save changes" :loading="loading" class="self-start" />
        </form>
    </UCard>

    <UCard>
        <form class="flex flex-col gap-4" @submit.prevent="onEmailSubmit">
          <h2 class="text-lg font-medium text-surface-900 dark:text-surface-0">Email address</h2>

          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Current email</label>
            <UInput :model-value="auth.user?.email" disabled class="w-full" />
          </div>

          <div class="flex flex-col gap-2">
            <label for="new-email" class="font-medium text-sm">New email</label>
            <UInput
              id="new-email"
              v-model="newEmail"
              :color="emailErrors.newEmail ? 'error' : undefined"
              class="w-full"
            />
            <UAlert
              v-if="emailErrors.newEmail"
              color="error"
              variant="subtle"
              :description="emailErrors.newEmail"
            />
          </div>

          <div class="flex flex-col gap-2">
            <label for="email-current-password" class="font-medium text-sm">Current password</label>
            <UInput
              id="email-current-password"
              v-model="emailCurrentPassword"
              :type="showEmailCurrentPassword ? 'text' : 'password'"
              :color="emailErrors.currentPassword ? 'error' : undefined"
              class="w-full"
              :ui="{ trailing: 'pe-1' }"
            >
              <template #trailing>
                <UButton
                  color="neutral"
                  variant="link"
                  size="sm"
                  :icon="showEmailCurrentPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                  :aria-label="showEmailCurrentPassword ? 'Hide password' : 'Show password'"
                  :aria-pressed="showEmailCurrentPassword"
                  @click="showEmailCurrentPassword = !showEmailCurrentPassword"
                />
              </template>
            </UInput>
            <UAlert
              v-if="emailErrors.currentPassword"
              color="error"
              variant="subtle"
              :description="emailErrors.currentPassword"
            />
          </div>

          <UAlert
            v-if="emailErrorMessage"
            color="error"
            variant="outline"
            :description="emailErrorMessage"
          />
          <UAlert
            v-if="emailSuccessMessage"
            color="success"
            variant="outline"
            :description="emailSuccessMessage"
          />

          <UButton
            type="submit"
            label="Update email"
            :loading="emailLoading"
            class="self-start"
          />
        </form>
    </UCard>

    <UCard>
        <form class="flex flex-col gap-4" @submit.prevent="onPasswordSubmit">
          <h2 class="text-lg font-medium text-surface-900 dark:text-surface-0">Password</h2>

          <div class="flex flex-col gap-2">
            <label for="password-current-password" class="font-medium text-sm">Current password</label>
            <UInput
              id="password-current-password"
              v-model="passwordCurrentPassword"
              :type="showPasswordCurrentPassword ? 'text' : 'password'"
              :color="passwordErrors.currentPassword ? 'error' : undefined"
              class="w-full"
              :ui="{ trailing: 'pe-1' }"
            >
              <template #trailing>
                <UButton
                  color="neutral"
                  variant="link"
                  size="sm"
                  :icon="showPasswordCurrentPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                  :aria-label="showPasswordCurrentPassword ? 'Hide password' : 'Show password'"
                  :aria-pressed="showPasswordCurrentPassword"
                  @click="showPasswordCurrentPassword = !showPasswordCurrentPassword"
                />
              </template>
            </UInput>
            <UAlert
              v-if="passwordErrors.currentPassword"
              color="error"
              variant="subtle"
              :description="passwordErrors.currentPassword"
            />
          </div>

          <div class="flex flex-col gap-2">
            <label for="new-password" class="font-medium text-sm">New password</label>
            <PasswordField
              id="new-password"
              v-model="newPassword"
              :invalid="!!passwordErrors.newPassword"
            />
            <UAlert
              v-if="passwordErrors.newPassword"
              color="error"
              variant="subtle"
              :description="passwordErrors.newPassword"
            />
          </div>

          <div class="flex flex-col gap-2">
            <label for="confirm-password" class="font-medium text-sm">Confirm new password</label>
            <UInput
              id="confirm-password"
              v-model="confirmPassword"
              :type="showConfirmPassword ? 'text' : 'password'"
              :color="passwordErrors.confirmPassword ? 'error' : undefined"
              class="w-full"
              :ui="{ trailing: 'pe-1' }"
            >
              <template #trailing>
                <UButton
                  color="neutral"
                  variant="link"
                  size="sm"
                  :icon="showConfirmPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'"
                  :aria-label="showConfirmPassword ? 'Hide password' : 'Show password'"
                  :aria-pressed="showConfirmPassword"
                  @click="showConfirmPassword = !showConfirmPassword"
                />
              </template>
            </UInput>
            <UAlert
              v-if="passwordErrors.confirmPassword"
              color="error"
              variant="subtle"
              :description="passwordErrors.confirmPassword"
            />
          </div>

          <UAlert
            v-if="passwordErrorMessage"
            color="error"
            variant="outline"
            :description="passwordErrorMessage"
          />
          <UAlert
            v-if="passwordSuccessMessage"
            color="success"
            variant="outline"
            :description="passwordSuccessMessage"
          />

          <UButton
            type="submit"
            label="Update password"
            :loading="passwordLoading"
            class="self-start"
          />
        </form>
    </UCard>

    <UCard>
        <div class="flex flex-col gap-4">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-medium text-surface-900 dark:text-surface-0">Passkeys</h2>
            <UButton
              label="Add a passkey"
              icon="i-lucide-plus"
              size="sm"
              @click="openAddPasskeyDialog"
            />
          </div>

          <p class="text-sm text-surface-500 dark:text-surface-400">
            Use a passkey to sign in without a password, on this device or others.
          </p>

          <UAlert
            v-if="credentialsError"
            color="error"
            variant="outline"
            :description="credentialsError"
          />

          <p v-if="!credentialsLoading && credentials.length === 0" class="text-sm text-surface-500 dark:text-surface-400">
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
    </UCard>

    <UCard>
        <div class="flex flex-col gap-4">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-medium text-surface-900 dark:text-surface-0">API keys</h2>
            <UButton
              label="Create API key"
              icon="i-lucide-plus"
              size="sm"
              @click="openAddApiKeyDialog"
            />
          </div>

          <p class="text-sm text-surface-500 dark:text-surface-400">
            Use an API key to authenticate requests to the API instead of signing in.
          </p>

          <UAlert
            v-if="apiKeysError"
            color="error"
            variant="outline"
            :description="apiKeysError"
          />

          <p v-if="!apiKeysLoading && apiKeys.length === 0" class="text-sm text-surface-500 dark:text-surface-400">
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
    </UCard>

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
  </div>
</template>
