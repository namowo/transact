<script setup lang="ts">
import { ref, watch } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { useAuthStore } from '@/stores/auth'
import { getErrorMessage } from '@/api/errors'

const auth = useAuthStore()

const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const localeCodes = ['en-US', 'en-GB', 'de-DE', 'de-AT', 'de-CH', 'fr-FR', 'es-ES', 'it-IT', 'nl-NL', 'pt-BR', 'sv-SE', 'da-DK', 'pl-PL']
const languageNames = new Intl.DisplayNames(['en'], { type: 'language' })
const localeOptions = localeCodes.map((code) => ({
  value: code,
  label: `${languageNames.of(code) ?? code} - ${new Intl.NumberFormat(code).format(1234.5)}`,
}))

const schema = yup.object({
  locale: yup.string().required(),
  firstName: yup.string().trim().required('First name is required.'),
  lastName: yup.string().trim().required('Last name is required.'),
})

const { defineField, errors, handleSubmit, resetForm } = useForm({
  validationSchema: schema,
  initialValues: { firstName: '', lastName: '', locale: 'en-US' },
})

const [firstName] = defineField('firstName')
const [lastName] = defineField('lastName')
const [locale] = defineField('locale')

watch(
  () => auth.user,
  (user) => {
    resetForm({
      values: {
        firstName: user?.first_name ?? '',
        lastName: user?.last_name ?? '',
        locale: user?.locale ?? 'en-US',
      },
    })
  },
  { immediate: true },
)

const onSubmit = handleSubmit(async (values) => {
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await auth.updateProfile({
      first_name: values.firstName.trim(),
      last_name: values.lastName.trim(),
      locale: values.locale,
    })
    successMessage.value = 'Profile updated.'
  } catch (err) {
    errorMessage.value = getErrorMessage(err, 'Could not update your profile. Please try again.')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <UCard>
    <template #header>
      <h2 class="text-lg font-semibold text-highlighted">Profile</h2>
      <p class="text-sm text-muted">Your name, number format and laboratory.</p>
    </template>
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
        <label for="locale" class="font-medium text-sm">Number format</label>
        <USelect id="locale" v-model="locale" :items="localeOptions" class="w-full" />
        <p class="text-sm text-surface-500 dark:text-surface-400">
          Decides how you type and read numbers, for example whether the decimal separator is a point or a
          comma. It is also the default for CSV downloads and uploads.
        </p>
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
</template>
