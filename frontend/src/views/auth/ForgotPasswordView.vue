<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Message from 'primevue/message'
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
    <Message severity="info" size="small">
      If an account matches <strong>{{ email }}</strong
      >, we've sent a password reset link to it.
    </Message>
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
      <InputText
        id="email"
        v-model="email"
        type="email"
        :invalid="!!errors.email"
        autofocus
        fluid
      />
      <Message v-if="errors.email" severity="error" size="small" variant="simple">
        {{ errors.email }}
      </Message>
    </div>
    <Button type="submit" label="Send reset link" :loading="loading" fluid />
    <p class="text-center text-sm">
      <RouterLink :to="{ name: 'login' }" class="text-primary no-underline hover:underline">
        Back to login
      </RouterLink>
    </p>
  </form>
</template>
