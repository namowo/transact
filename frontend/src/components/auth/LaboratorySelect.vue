<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Select from 'primevue/select'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { createLaboratory, listLaboratories } from '@/api/laboratories'
import type { Laboratory } from '@/api/types'
import { COUNTRIES } from '@/constants/countries'

const modelValue = defineModel<number | null>({ default: null })

const laboratories = ref<Laboratory[]>([])
const loading = ref(false)
const loadError = ref('')

const dialogVisible = ref(false)
const submitting = ref(false)
const submitError = ref('')

const laboratorySchema = yup.object({
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

const { defineField, errors, handleSubmit, resetForm } = useForm({
  validationSchema: laboratorySchema,
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

const [laboratoryName, laboratoryNameAttrs] = defineField('laboratory_name')
const [institutionalAffiliation, institutionalAffiliationAttrs] = defineField(
  'institutional_affiliation',
)
const [directorHeadOfLaboratory, directorHeadOfLaboratoryAttrs] = defineField(
  'director_head_of_laboratory',
)
const [streetAddress, streetAddressAttrs] = defineField('street_address')
const [city, cityAttrs] = defineField('city')
const [state, stateAttrs] = defineField('state')
const [postalCode, postalCodeAttrs] = defineField('postal_code')
const [country, countryAttrs] = defineField('country')
const [email, emailAttrs] = defineField('email')

async function loadLaboratories() {
  loading.value = true
  loadError.value = ''
  try {
    laboratories.value = await listLaboratories()
  } catch {
    loadError.value = 'Could not load laboratories.'
  } finally {
    loading.value = false
  }
}

onMounted(loadLaboratories)

function openDialog() {
  resetForm()
  submitError.value = ''
  dialogVisible.value = true
}

const submitNewLaboratory = handleSubmit(async (values) => {
  submitting.value = true
  submitError.value = ''
  try {
    const created = await createLaboratory({
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
    laboratories.value.push(created)
    modelValue.value = created.id
    dialogVisible.value = false
  } catch {
    submitError.value = 'Could not create the laboratory. Please try again.'
  } finally {
    submitting.value = false
  }
})
</script>

<template>
  <div>
    <Select
      v-model="modelValue"
      :options="laboratories"
      option-label="laboratory_name"
      option-value="id"
      filter
      show-clear
      :loading="loading"
      placeholder="Select your laboratory"
      class="w-full"
      fluid
    />
    <Message v-if="loadError" severity="error" size="small" variant="simple" class="mt-1">
      {{ loadError }}
    </Message>
    <Button
      label="Laboratory not listed? Add it"
      link
      size="small"
      class="!p-0 mt-2"
      @click="openDialog"
    />

    <Dialog v-model:visible="dialogVisible" header="Add laboratory" modal :style="{ width: '28rem' }">
      <form class="flex flex-col gap-4" @submit.prevent="submitNewLaboratory">
        <div class="flex flex-col gap-2">
          <label for="lab-name" class="font-medium text-sm">Laboratory name *</label>
          <InputText
            id="lab-name"
            v-model="laboratoryName"
            v-bind="laboratoryNameAttrs"
            :invalid="!!errors.laboratory_name"
            fluid
            autofocus
          />
          <Message v-if="errors.laboratory_name" severity="error" size="small" variant="simple">
            {{ errors.laboratory_name }}
          </Message>
        </div>
        <div class="flex flex-col gap-2">
          <label for="lab-affiliation" class="font-medium text-sm">Institutional affiliation *</label>
          <InputText
            id="lab-affiliation"
            v-model="institutionalAffiliation"
            v-bind="institutionalAffiliationAttrs"
            :invalid="!!errors.institutional_affiliation"
            fluid
          />
          <Message
            v-if="errors.institutional_affiliation"
            severity="error"
            size="small"
            variant="simple"
          >
            {{ errors.institutional_affiliation }}
          </Message>
        </div>
        <div class="flex flex-col gap-2">
          <label for="lab-director" class="font-medium text-sm">Director / Head of laboratory</label>
          <InputText
            id="lab-director"
            v-model="directorHeadOfLaboratory"
            v-bind="directorHeadOfLaboratoryAttrs"
            :invalid="!!errors.director_head_of_laboratory"
            fluid
          />
          <Message
            v-if="errors.director_head_of_laboratory"
            severity="error"
            size="small"
            variant="simple"
          >
            {{ errors.director_head_of_laboratory }}
          </Message>
        </div>
        <div class="flex flex-col gap-2">
          <label for="lab-email" class="font-medium text-sm">Email</label>
          <InputText
            id="lab-email"
            v-model="email"
            v-bind="emailAttrs"
            type="email"
            :invalid="!!errors.email"
            fluid
          />
          <Message v-if="errors.email" severity="error" size="small" variant="simple">
            {{ errors.email }}
          </Message>
        </div>
        <div class="flex flex-col gap-2">
          <label for="lab-street" class="font-medium text-sm">Street address</label>
          <InputText
            id="lab-street"
            v-model="streetAddress"
            v-bind="streetAddressAttrs"
            :invalid="!!errors.street_address"
            fluid
          />
          <Message v-if="errors.street_address" severity="error" size="small" variant="simple">
            {{ errors.street_address }}
          </Message>
        </div>
        <div class="flex flex-col sm:flex-row gap-4">
          <div class="flex flex-col gap-2 flex-1">
            <label for="lab-city" class="font-medium text-sm">City *</label>
            <InputText
              id="lab-city"
              v-model="city"
              v-bind="cityAttrs"
              :invalid="!!errors.city"
              fluid
            />
            <Message v-if="errors.city" severity="error" size="small" variant="simple">
              {{ errors.city }}
            </Message>
          </div>
          <div class="flex flex-col gap-2 flex-1">
            <label for="lab-postal-code" class="font-medium text-sm">Postal code</label>
            <InputText
              id="lab-postal-code"
              v-model="postalCode"
              v-bind="postalCodeAttrs"
              :invalid="!!errors.postal_code"
              fluid
            />
            <Message v-if="errors.postal_code" severity="error" size="small" variant="simple">
              {{ errors.postal_code }}
            </Message>
          </div>
        </div>
        <div class="flex flex-col sm:flex-row gap-4">
          <div class="flex flex-col gap-2 flex-1">
            <label for="lab-state" class="font-medium text-sm">State</label>
            <InputText
              id="lab-state"
              v-model="state"
              v-bind="stateAttrs"
              :invalid="!!errors.state"
              fluid
            />
            <Message v-if="errors.state" severity="error" size="small" variant="simple">
              {{ errors.state }}
            </Message>
          </div>
          <div class="flex flex-col gap-2 flex-1">
            <label for="lab-country" class="font-medium text-sm">Country *</label>
            <Select
              id="lab-country"
              v-model="country"
              v-bind="countryAttrs"
              :options="COUNTRIES"
              filter
              placeholder="Select country"
              :invalid="!!errors.country"
              fluid
            />
            <Message v-if="errors.country" severity="error" size="small" variant="simple">
              {{ errors.country }}
            </Message>
          </div>
        </div>
        <Message v-if="submitError" severity="error" size="small">{{ submitError }}</Message>
      </form>
      <template #footer>
        <Button label="Cancel" text @click="dialogVisible = false" />
        <Button label="Add laboratory" :loading="submitting" @click="submitNewLaboratory" />
      </template>
    </Dialog>
  </div>
</template>
