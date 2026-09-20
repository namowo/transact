<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { forgotPassword } from '@/api/auth'

const loading = ref(false)
const done = ref(false)

const schema = yup.object({
  email: yup.string().trim().email('Please enter a valid email address.').required(),
})

const { defineField, errors, handleSubmit } = useForm({
  validationSchema: schema,
  initialValues: { email: '' },
})

const [email] = defineField('email')

const onSubmit = handleSubmit(async (values) => {
  loading.value = true
  try {
    await forgotPassword(values.email.trim())
  } finally {
    loading.value = false
    // Always show the same confirmation, regardless of whether the
    // address matched an account, so we don't leak which emails are registered.
    done.value = true
  }
})
</script>

<template>
  <div v-if="done" class="flex flex-col gap-4 text-center">
    <i class="pi pi-envelope text-4xl text-primary" />
    <UAlert color="info" variant="outline">
      <template #description>
        If an account matches <strong>{{ email }}</strong
        >, we've sent a password reset link to it.
      </template>
    </UAlert>
    <RouterLink :to="{ name: 'login' }" class="text-primary no-underline hover:underline">
      Back to login
    </RouterLink>
  </div>

  <form v-else class="flex flex-col gap-6" @submit.prevent="onSubmit">
    <div class="flex flex-col gap-1">
      <h1 class="text-3xl font-medium text-surface-900 dark:text-surface-0">Forgot password?</h1>
      <p class="text-sm text-surface-500 dark:text-surface-400">
        Enter your email address and we'll send you a link to reset your password
      </p>
    </div>
    <div class="flex flex-col gap-2">
      <label for="email" class="font-medium text-sm">Email</label>
      <UInput
        id="email"
        v-model="email"
        type="email"
        :color="errors.email ? 'error' : undefined"
        autofocus
        class="w-full"
      />
      <UAlert v-if="errors.email" color="error" variant="subtle" :description="errors.email" />
    </div>
    <UButton type="submit" label="Send reset link" :loading="loading" block />
    <p class="text-center text-sm">
      <RouterLink :to="{ name: 'login' }" class="text-primary no-underline hover:underline">
        Back to login
      </RouterLink>
    </p>
  </form>
</template>
