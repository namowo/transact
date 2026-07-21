<script setup lang="ts">
import { onMounted, ref, watchEffect } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { startRegistration } from '@simplewebauthn/browser'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Dialog from 'primevue/dialog'
import { useAuthStore } from '@/stores/auth'
import { getErrorMessage } from '@/api/errors'
import * as webauthnApi from '@/api/webauthn'
import type { WebAuthnCredential } from '@/api/types'

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

    <Card>
      <template #content>
        <form class="flex flex-col gap-4" @submit.prevent="onSubmit">
          <div class="flex flex-col sm:flex-row gap-4">
            <div class="flex flex-col gap-2 flex-1">
              <label for="first-name" class="font-medium text-sm">First name</label>
              <InputText id="first-name" v-model="firstName" :invalid="!!errors.firstName" fluid />
              <Message v-if="errors.firstName" severity="error" size="small" variant="simple">
                {{ errors.firstName }}
              </Message>
            </div>
            <div class="flex flex-col gap-2 flex-1">
              <label for="last-name" class="font-medium text-sm">Last name</label>
              <InputText id="last-name" v-model="lastName" :invalid="!!errors.lastName" fluid />
              <Message v-if="errors.lastName" severity="error" size="small" variant="simple">
                {{ errors.lastName }}
              </Message>
            </div>
          </div>

          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Laboratory</label>
            <InputText :model-value="auth.user?.laboratory?.laboratory_name" disabled fluid />
          </div>

          <Message v-if="errorMessage" severity="error" size="small">{{ errorMessage }}</Message>
          <Message v-if="successMessage" severity="success" size="small">{{
            successMessage
          }}</Message>

          <Button type="submit" label="Save changes" :loading="loading" class="self-start" />
        </form>
      </template>
    </Card>

    <Card>
      <template #content>
        <form class="flex flex-col gap-4" @submit.prevent="onEmailSubmit">
          <h2 class="text-lg font-medium text-surface-900 dark:text-surface-0">Email address</h2>

          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Current email</label>
            <InputText :model-value="auth.user?.email" disabled fluid />
          </div>

          <div class="flex flex-col gap-2">
            <label for="new-email" class="font-medium text-sm">New email</label>
            <InputText id="new-email" v-model="newEmail" :invalid="!!emailErrors.newEmail" fluid />
            <Message v-if="emailErrors.newEmail" severity="error" size="small" variant="simple">
              {{ emailErrors.newEmail }}
            </Message>
          </div>

          <div class="flex flex-col gap-2">
            <label for="email-current-password" class="font-medium text-sm">Current password</label>
            <Password
              input-id="email-current-password"
              v-model="emailCurrentPassword"
              toggle-mask
              :feedback="false"
              fluid
              :invalid="!!emailErrors.currentPassword"
            />
            <Message v-if="emailErrors.currentPassword" severity="error" size="small" variant="simple">
              {{ emailErrors.currentPassword }}
            </Message>
          </div>

          <Message v-if="emailErrorMessage" severity="error" size="small">{{ emailErrorMessage }}</Message>
          <Message v-if="emailSuccessMessage" severity="success" size="small">{{
            emailSuccessMessage
          }}</Message>

          <Button
            type="submit"
            label="Update email"
            :loading="emailLoading"
            class="self-start"
          />
        </form>
      </template>
    </Card>

    <Card>
      <template #content>
        <form class="flex flex-col gap-4" @submit.prevent="onPasswordSubmit">
          <h2 class="text-lg font-medium text-surface-900 dark:text-surface-0">Password</h2>

          <div class="flex flex-col gap-2">
            <label for="password-current-password" class="font-medium text-sm">Current password</label>
            <Password
              input-id="password-current-password"
              v-model="passwordCurrentPassword"
              toggle-mask
              :feedback="false"
              fluid
              :invalid="!!passwordErrors.currentPassword"
            />
            <Message v-if="passwordErrors.currentPassword" severity="error" size="small" variant="simple">
              {{ passwordErrors.currentPassword }}
            </Message>
          </div>

          <div class="flex flex-col gap-2">
            <label for="new-password" class="font-medium text-sm">New password</label>
            <Password
              input-id="new-password"
              v-model="newPassword"
              toggle-mask
              fluid
              :invalid="!!passwordErrors.newPassword"
            />
            <Message v-if="passwordErrors.newPassword" severity="error" size="small" variant="simple">
              {{ passwordErrors.newPassword }}
            </Message>
          </div>

          <div class="flex flex-col gap-2">
            <label for="confirm-password" class="font-medium text-sm">Confirm new password</label>
            <Password
              input-id="confirm-password"
              v-model="confirmPassword"
              toggle-mask
              :feedback="false"
              fluid
              :invalid="!!passwordErrors.confirmPassword"
            />
            <Message v-if="passwordErrors.confirmPassword" severity="error" size="small" variant="simple">
              {{ passwordErrors.confirmPassword }}
            </Message>
          </div>

          <Message v-if="passwordErrorMessage" severity="error" size="small">{{
            passwordErrorMessage
          }}</Message>
          <Message v-if="passwordSuccessMessage" severity="success" size="small">{{
            passwordSuccessMessage
          }}</Message>

          <Button
            type="submit"
            label="Update password"
            :loading="passwordLoading"
            class="self-start"
          />
        </form>
      </template>
    </Card>

    <Card>
      <template #content>
        <div class="flex flex-col gap-4">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-medium text-surface-900 dark:text-surface-0">Passkeys</h2>
            <Button
              label="Add a passkey"
              icon="pi pi-plus"
              size="small"
              @click="openAddPasskeyDialog"
            />
          </div>

          <p class="text-sm text-surface-500 dark:text-surface-400">
            Use a passkey to sign in without a password, on this device or others.
          </p>

          <Message v-if="credentialsError" severity="error" size="small">{{
            credentialsError
          }}</Message>

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
              <Button
                icon="pi pi-trash"
                severity="danger"
                text
                @click="onDeletePasskey(credential)"
              />
            </li>
          </ul>
        </div>
      </template>
    </Card>

    <Dialog v-model:visible="showAddPasskeyDialog" modal header="Add a passkey" style="width: 28rem">
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label for="device-name" class="font-medium text-sm">Device name (optional)</label>
          <InputText id="device-name" v-model="newDeviceName" placeholder="e.g. MacBook Pro" fluid />
        </div>
        <Message v-if="credentialsError" severity="error" size="small">{{ credentialsError }}</Message>
      </div>
      <template #footer>
        <Button label="Cancel" text @click="showAddPasskeyDialog = false" />
        <Button label="Continue" :loading="addingPasskey" @click="onAddPasskey" />
      </template>
    </Dialog>
  </div>
</template>
