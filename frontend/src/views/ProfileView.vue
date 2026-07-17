<script setup lang="ts">
import { ref, watchEffect } from 'vue'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { useAuthStore } from '@/stores/auth'
import { getErrorMessage } from '@/api/errors'

const auth = useAuthStore()

const firstName = ref('')
const lastName = ref('')

const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

watchEffect(() => {
  firstName.value = auth.user?.first_name ?? ''
  lastName.value = auth.user?.last_name ?? ''
})

async function onSubmit() {
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await auth.updateProfile({
      first_name: firstName.value,
      last_name: lastName.value,
    })
    successMessage.value = 'Profile updated.'
  } catch (err) {
    errorMessage.value = getErrorMessage(err, 'Could not update your profile. Please try again.')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 max-w-lg">
    <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Edit profile</h1>

    <Card>
      <template #content>
        <form class="flex flex-col gap-4" @submit.prevent="onSubmit">
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Email</label>
            <InputText :model-value="auth.user?.email" disabled fluid />
          </div>

          <div class="flex flex-col sm:flex-row gap-4">
            <div class="flex flex-col gap-2 flex-1">
              <label for="first-name" class="font-medium text-sm">First name</label>
              <InputText id="first-name" v-model="firstName" required fluid />
            </div>
            <div class="flex flex-col gap-2 flex-1">
              <label for="last-name" class="font-medium text-sm">Last name</label>
              <InputText id="last-name" v-model="lastName" required fluid />
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
  </div>
</template>
