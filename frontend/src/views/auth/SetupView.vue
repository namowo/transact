<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import PasswordField from '@/components/auth/PasswordField.vue'
import { useAuthStore } from '@/stores/auth'
import { getErrorMessage } from '@/api/errors'

const auth = useAuthStore()
const router = useRouter()

const errorMessage = ref('')

const schema = yup.object({
  first_name: yup.string().trim().required('First name is required.'),
  last_name: yup.string().trim().required('Last name is required.'),
  email: yup
    .string()
    .trim()
    .email('Please enter a valid email address.')
    .required('Email is required.'),
  password: yup
    .string()
    .required('Password is required.')
    .min(8, 'Password must be at least 8 characters.')
    .matches(/\d/, 'Password must contain a number.')
    .matches(/[A-Z]/, 'Password must contain an uppercase letter.')
    .matches(/[^a-zA-Z0-9]/, 'Password must contain a special character.'),
})

const { defineField, errors, handleSubmit, isSubmitting } = useForm({
  validationSchema: schema,
  initialValues: { first_name: '', last_name: '', email: '', password: '' },
})

const [firstName, firstNameAttrs] = defineField('first_name')
const [lastName, lastNameAttrs] = defineField('last_name')
const [email, emailAttrs] = defineField('email')
const [password] = defineField('password')

const onSubmit = handleSubmit(async (values) => {
  errorMessage.value = ''
  try {
    await auth.completeSetup({
      email: values.email.trim(),
      password: values.password,
      first_name: values.first_name.trim(),
      last_name: values.last_name.trim(),
    })
    router.push({ name: 'dashboard' })
  } catch (err) {
    errorMessage.value = getErrorMessage(err, 'Could not complete setup. Please try again.')
  }
})
</script>

<template>
  <form class="flex flex-col gap-6" @submit.prevent="onSubmit">
    <div class="flex flex-col gap-1">
      <h1 class="text-3xl font-medium text-surface-900 dark:text-surface-0">Welcome to TransAct</h1>
      <p class="text-sm text-surface-500 dark:text-surface-400">
        Create the administrator account to finish setting up this instance.
      </p>
    </div>

    <div class="flex flex-col sm:flex-row gap-4">
      <div class="flex flex-col gap-2 flex-1">
        <label for="first-name" class="font-medium text-sm">First name</label>
        <UInput
          id="first-name"
          v-model="firstName"
          v-bind="firstNameAttrs"
          :color="errors.first_name ? 'error' : undefined"
          autofocus
          class="w-full"
        />
        <UAlert
          v-if="errors.first_name"
          color="error"
          variant="subtle"
          :description="errors.first_name"
        />
      </div>
      <div class="flex flex-col gap-2 flex-1">
        <label for="last-name" class="font-medium text-sm">Last name</label>
        <UInput
          id="last-name"
          v-model="lastName"
          v-bind="lastNameAttrs"
          :color="errors.last_name ? 'error' : undefined"
          class="w-full"
        />
        <UAlert
          v-if="errors.last_name"
          color="error"
          variant="subtle"
          :description="errors.last_name"
        />
      </div>
    </div>

    <div class="flex flex-col gap-2">
      <label for="email" class="font-medium text-sm">Email</label>
      <UInput
        id="email"
        v-model="email"
        v-bind="emailAttrs"
        type="email"
        :color="errors.email ? 'error' : undefined"
        class="w-full"
      />
      <UAlert v-if="errors.email" color="error" variant="subtle" :description="errors.email" />
    </div>

    <div class="flex flex-col gap-2">
      <label class="font-medium text-sm">Create a password</label>
      <PasswordField v-model="password" :invalid="!!errors.password" />
    </div>

    <UAlert v-if="errorMessage" color="error" variant="outline" :description="errorMessage" />

    <UButton type="submit" label="Create administrator account" :loading="isSubmitting" block />
  </form>
</template>
