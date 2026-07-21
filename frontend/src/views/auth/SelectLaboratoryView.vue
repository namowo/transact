<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import Button from 'primevue/button'
import Message from 'primevue/message'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import SelectButton from 'primevue/selectbutton'
import LaboratorySelect from '@/components/auth/LaboratorySelect.vue'
import {
  fetchMyMembershipRequest,
  joinExistingLab,
  requestNewLaboratory,
} from '@/api/labMembershipRequests'
import type { LabMembershipRequest } from '@/api/types'
import { getErrorMessage } from '@/api/errors'
import { COUNTRIES } from '@/constants/countries'

const loading = ref(true)
const pendingRequest = ref<LabMembershipRequest | null>(null)
const submitted = ref(false)

const mode = ref<'join' | 'new'>('join')
const modeOptions = [
  { label: 'Join an existing laboratory', value: 'join' },
  { label: 'Request a new laboratory', value: 'new' },
]

const joinErrorMessage = ref('')
const joinLaboratoryId = ref<number | null>(null)
const joinTouched = ref(false)
const joining = ref(false)

async function submitJoin() {
  joinTouched.value = true
  if (!joinLaboratoryId.value) return
  joining.value = true
  joinErrorMessage.value = ''
  try {
    pendingRequest.value = await joinExistingLab({ laboratory_id: joinLaboratoryId.value })
    submitted.value = true
  } catch (err) {
    joinErrorMessage.value = getErrorMessage(
      err,
      'Could not submit your request. Please try again.',
    )
  } finally {
    joining.value = false
  }
}

const newLabSchema = yup.object({
  laboratory_name: yup.string().trim().required('Laboratory name is required.'),
  institutional_affiliation: yup
    .string()
    .trim()
    .required('Institutional affiliation is required.'),
  director_head_of_laboratory: yup.string().trim().defined(),
  street_address: yup.string().trim().defined(),
  city: yup.string().trim().required('City is required.'),
  state: yup.string().trim().defined(),
  postal_code: yup.string().trim().defined(),
  country: yup.string().trim().required('Country is required.'),
  email: yup.string().trim().email('Please enter a valid email address.').defined(),
})

const {
  defineField,
  errors: newLabErrors,
  handleSubmit: handleNewLabSubmit,
  isSubmitting: submittingNewLab,
} = useForm({
  validationSchema: newLabSchema,
  initialValues: {
    laboratory_name: '',
    institutional_affiliation: '',
    director_head_of_laboratory: '',
    street_address: '',
    city: '',
    state: '',
    postal_code: '',
    country: '',
    email: '',
  },
})

const [laboratoryName] = defineField('laboratory_name')
const [institutionalAffiliation] = defineField('institutional_affiliation')
const [directorHeadOfLaboratory] = defineField('director_head_of_laboratory')
const [streetAddress] = defineField('street_address')
const [city] = defineField('city')
const [state] = defineField('state')
const [postalCode] = defineField('postal_code')
const [country] = defineField('country')
const [email] = defineField('email')

const newLabErrorMessage = ref('')

const submitNewLab = handleNewLabSubmit(async (values) => {
  newLabErrorMessage.value = ''
  try {
    pendingRequest.value = await requestNewLaboratory({
      laboratory_name: values.laboratory_name.trim(),
      institutional_affiliation: values.institutional_affiliation.trim(),
      director_head_of_laboratory: values.director_head_of_laboratory.trim() || null,
      street_address: values.street_address.trim() || null,
      city: values.city.trim(),
      state: values.state.trim() || null,
      postal_code: values.postal_code.trim() || null,
      country: values.country.trim(),
      email: values.email.trim() || null,
    })
    submitted.value = true
  } catch (err) {
    newLabErrorMessage.value = getErrorMessage(
      err,
      'Could not submit your request. Please try again.',
    )
  }
})

onMounted(async () => {
  try {
    pendingRequest.value = await fetchMyMembershipRequest()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <div v-if="loading" class="flex flex-col gap-1">
      <p class="text-sm text-surface-500 dark:text-surface-400">Loading...</p>
    </div>

    <template v-else-if="pendingRequest || submitted">
      <div class="flex flex-col gap-1">
        <h1 class="text-3xl font-medium text-surface-900 dark:text-surface-0">Request pending</h1>
        <p class="text-sm text-surface-500 dark:text-surface-400">
          Your request to join
          <strong>{{ pendingRequest?.laboratory.laboratory_name }}</strong>
          is awaiting review. You'll receive an email once it has been reviewed.
        </p>
      </div>
    </template>

    <template v-else>
      <div class="flex flex-col gap-1">
        <h1 class="text-3xl font-medium text-surface-900 dark:text-surface-0">
          Select your laboratory
        </h1>
        <p class="text-sm text-surface-500 dark:text-surface-400">
          Join an existing laboratory or request a new one. Your request will need to be
          approved before you can continue.
        </p>
      </div>

      <SelectButton v-model="mode" :options="modeOptions" option-label="label" option-value="value" />

      <form v-if="mode === 'join'" class="flex flex-col gap-6" @submit.prevent="submitJoin">
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Laboratory</label>
          <LaboratorySelect v-model="joinLaboratoryId" />
          <Message
            v-if="joinTouched && !joinLaboratoryId"
            severity="error"
            size="small"
            variant="simple"
          >
            Please select your laboratory.
          </Message>
        </div>

        <Message v-if="joinErrorMessage" severity="error" size="small">
          {{ joinErrorMessage }}
        </Message>

        <Button type="submit" label="Request to join" :loading="joining" fluid />
      </form>

      <form v-else class="flex flex-col gap-4" @submit.prevent="submitNewLab">
        <div class="flex flex-col gap-2">
          <label for="lab-name" class="font-medium text-sm">Laboratory name *</label>
          <InputText
            id="lab-name"
            v-model="laboratoryName"
            :invalid="!!newLabErrors.laboratory_name"
            fluid
          />
          <Message v-if="newLabErrors.laboratory_name" severity="error" size="small" variant="simple">
            {{ newLabErrors.laboratory_name }}
          </Message>
        </div>
        <div class="flex flex-col gap-2">
          <label for="lab-affiliation" class="font-medium text-sm">
            Institutional affiliation *
          </label>
          <InputText
            id="lab-affiliation"
            v-model="institutionalAffiliation"
            :invalid="!!newLabErrors.institutional_affiliation"
            fluid
          />
          <Message
            v-if="newLabErrors.institutional_affiliation"
            severity="error"
            size="small"
            variant="simple"
          >
            {{ newLabErrors.institutional_affiliation }}
          </Message>
        </div>
        <div class="flex flex-col gap-2">
          <label for="lab-director" class="font-medium text-sm">
            Director / Head of laboratory
          </label>
          <InputText id="lab-director" v-model="directorHeadOfLaboratory" fluid />
        </div>
        <div class="flex flex-col gap-2">
          <label for="lab-email" class="font-medium text-sm">Email</label>
          <InputText
            id="lab-email"
            v-model="email"
            type="email"
            :invalid="!!newLabErrors.email"
            fluid
          />
          <Message v-if="newLabErrors.email" severity="error" size="small" variant="simple">
            {{ newLabErrors.email }}
          </Message>
        </div>
        <div class="flex flex-col gap-2">
          <label for="lab-street" class="font-medium text-sm">Street address</label>
          <InputText id="lab-street" v-model="streetAddress" fluid />
        </div>
        <div class="flex flex-col sm:flex-row gap-4">
          <div class="flex flex-col gap-2 flex-1">
            <label for="lab-city" class="font-medium text-sm">City *</label>
            <InputText id="lab-city" v-model="city" :invalid="!!newLabErrors.city" fluid />
            <Message v-if="newLabErrors.city" severity="error" size="small" variant="simple">
              {{ newLabErrors.city }}
            </Message>
          </div>
          <div class="flex flex-col gap-2 flex-1">
            <label for="lab-postal-code" class="font-medium text-sm">Postal code</label>
            <InputText id="lab-postal-code" v-model="postalCode" fluid />
          </div>
        </div>
        <div class="flex flex-col sm:flex-row gap-4">
          <div class="flex flex-col gap-2 flex-1">
            <label for="lab-state" class="font-medium text-sm">State</label>
            <InputText id="lab-state" v-model="state" fluid />
          </div>
          <div class="flex flex-col gap-2 flex-1">
            <label for="lab-country" class="font-medium text-sm">Country *</label>
            <Select
              id="lab-country"
              v-model="country"
              :options="COUNTRIES"
              filter
              placeholder="Select country"
              :invalid="!!newLabErrors.country"
              fluid
            />
            <Message v-if="newLabErrors.country" severity="error" size="small" variant="simple">
              {{ newLabErrors.country }}
            </Message>
          </div>
        </div>

        <Message v-if="newLabErrorMessage" severity="error" size="small">
          {{ newLabErrorMessage }}
        </Message>

        <Button type="submit" label="Request new laboratory" :loading="submittingNewLab" fluid />
      </form>
    </template>
  </div>
</template>
