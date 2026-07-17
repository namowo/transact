<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import Button from 'primevue/button'
import Message from 'primevue/message'
import LaboratorySelect from '@/components/auth/LaboratorySelect.vue'
import { useAuthStore } from '@/stores/auth'
import { getErrorMessage } from '@/api/errors'
import { ref } from 'vue'

const auth = useAuthStore()
const router = useRouter()
const errorMessage = ref('')

const schema = yup.object({
  laboratory_id: yup
    .number()
    .typeError('Please select or add your laboratory.')
    .required('Please select or add your laboratory.'),
})

const { defineField, errors, handleSubmit, isSubmitting } = useForm({
  validationSchema: schema,
  initialValues: { laboratory_id: null },
})

const [laboratoryId] = defineField('laboratory_id')

const onSubmit = handleSubmit(async (values) => {
  errorMessage.value = ''
  try {
    await auth.updateProfile({ laboratory_id: values.laboratory_id ?? undefined })
    await router.push({ name: 'dashboard' })
  } catch (err) {
    errorMessage.value = getErrorMessage(err, 'Could not save your laboratory. Please try again.')
  }
})
</script>

<template>
  <form class="flex flex-col gap-6" @submit.prevent="onSubmit">
    <div class="flex flex-col gap-1">
      <h1 class="text-3xl font-medium text-surface-900 dark:text-surface-0">
        Select your laboratory
      </h1>
      <p class="text-sm text-surface-500 dark:text-surface-400">
        Choose your laboratory to continue. If it's not listed yet, you can add it.
      </p>
    </div>

    <div class="flex flex-col gap-2">
      <label class="font-medium text-sm">Laboratory</label>
      <LaboratorySelect v-model="laboratoryId" />
      <Message v-if="errors.laboratory_id" severity="error" size="small" variant="simple">
        {{ errors.laboratory_id }}
      </Message>
    </div>

    <Message v-if="errorMessage" severity="error" size="small">{{ errorMessage }}</Message>

    <Button type="submit" label="Continue" :loading="isSubmitting" fluid />
  </form>
</template>
