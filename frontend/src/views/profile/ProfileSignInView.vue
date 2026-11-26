<script setup lang="ts">
import { ref } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import PasswordField from '@/components/auth/PasswordField.vue'
import { useAuthStore } from '@/stores/auth'
import { getErrorMessage } from '@/api/errors'

const auth = useAuthStore()

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
  <div class="flex flex-col gap-6">
    <UCard>
      <template #header>
        <h2 class="text-lg font-semibold text-highlighted">Email address</h2>
        <p class="text-sm text-muted">The address you sign in with and receive emails at.</p>
      </template>
        <form class="flex flex-col gap-4" @submit.prevent="onEmailSubmit">
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
      <template #header>
        <h2 class="text-lg font-semibold text-highlighted">Password</h2>
        <p class="text-sm text-muted">Change the password you sign in with.</p>
      </template>
        <form class="flex flex-col gap-4" @submit.prevent="onPasswordSubmit">
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
  </div>
</template>
