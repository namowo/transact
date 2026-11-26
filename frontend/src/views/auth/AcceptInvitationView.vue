<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import PasswordField from '@/components/auth/PasswordField.vue'
import { getErrorMessage } from '@/api/errors'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const token = (route.query.token as string | undefined) ?? ''
const loading = ref(false)
const errorMessage = ref(token ? '' : 'This invitation link is missing its token.')

const schema = yup.object({
  password: yup
    .string()
    .required('Password is required.')
    .min(8, 'Password must be at least 8 characters.')
    .matches(/\d/, 'Password must contain a number.')
    .matches(/[A-Z]/, 'Password must contain an uppercase letter.')
    .matches(/[^a-zA-Z0-9]/, 'Password must contain a special character.'),
})

const { defineField, errors, handleSubmit } = useForm({
  validationSchema: schema,
  initialValues: { password: '' },
})

const [password] = defineField('password')

const onSubmit = handleSubmit(async (values) => {
  if (!token) return
  loading.value = true
  errorMessage.value = ''
  try {
    await auth.acceptInvitation(token, values.password)
    await router.replace({ name: 'dashboard' })
  } catch (err) {
    errorMessage.value = getErrorMessage(err, 'This invitation link is invalid or has expired.')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <form class="flex flex-col gap-6" @submit.prevent="onSubmit">
    <div class="flex flex-col gap-1">
      <h1 class="text-3xl font-medium text-surface-900 dark:text-surface-0">Accept invitation</h1>
      <p class="text-sm text-surface-500 dark:text-surface-400">
        Choose a password to activate your account
      </p>
    </div>
    <div class="flex flex-col gap-2">
      <label for="password" class="font-medium text-sm">Password</label>
      <PasswordField
        id="password"
        v-model="password"
        :invalid="!!errors.password"
        :disabled="!token"
      />
      <UAlert v-if="errors.password" color="error" variant="subtle" :description="errors.password" />
    </div>
    <UAlert v-if="errorMessage" color="error" variant="outline" :description="errorMessage">
      <template #actions>
        <span class="text-sm">
          Ask whoever invited you for a new link, or
          <RouterLink :to="{ name: 'forgot-password' }" class="text-primary hover:underline">
            reset your password
          </RouterLink>.
        </span>
      </template>
    </UAlert>
    <UButton
      type="submit"
      label="Activate account"
      :loading="loading"
      :disabled="!token"
      block
    />
    <p class="text-center text-sm">
      <RouterLink :to="{ name: 'login' }" class="text-primary no-underline hover:underline">
        Back to login
      </RouterLink>
    </p>
  </form>
</template>
