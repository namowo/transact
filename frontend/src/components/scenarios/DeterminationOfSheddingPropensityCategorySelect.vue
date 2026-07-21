<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import Select from 'primevue/select'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Message from 'primevue/message'
import { determinationOfSheddingPropensityCategoryApi } from '@/api/categories'
import type { DeterminationOfSheddingPropensityCategory } from '@/api/types'

const modelValue = defineModel<number | null>({ default: null })

const options = ref<DeterminationOfSheddingPropensityCategory[]>([])
const loading = ref(false)

// These records don't have a "name" - label them by title, falling back to
// authors or the record id so every option in the dropdown is identifiable.
const selectOptions = computed(() =>
  options.value.map((option) => ({
    id: option.id,
    label: option.title || option.authors || `Reference #${option.id}`,
  })),
)

async function load() {
  loading.value = true
  try {
    options.value = await determinationOfSheddingPropensityCategoryApi.list()
  } finally {
    loading.value = false
  }
}

onMounted(load)

interface FormState {
  authors: string
  title: string
  doi: string
  restrictions_prior_to_sampling: string
  monitored_transfer_factors: string
  number_of_participants: string
  replicates: string
  shedder_test: string
  classification_criteria: string
  classification_scheme: string
  classification_outcome: string
}

function emptyForm(): FormState {
  return {
    authors: '',
    title: '',
    doi: '',
    restrictions_prior_to_sampling: '',
    monitored_transfer_factors: '',
    number_of_participants: '',
    replicates: '',
    shedder_test: '',
    classification_criteria: '',
    classification_scheme: '',
    classification_outcome: '',
  }
}

// Either a title or an author identifies the reference - neither field is
// required on its own, but at least one of the two must be filled in.
const schema = yup.object({
  authors: yup.string().trim().defined(),
  title: yup.string().trim().defined(),
  doi: yup.string().trim().defined(),
  restrictions_prior_to_sampling: yup.string().trim().defined(),
  monitored_transfer_factors: yup.string().trim().defined(),
  number_of_participants: yup.string().trim().defined(),
  replicates: yup.string().trim().defined(),
  shedder_test: yup.string().trim().defined(),
  classification_criteria: yup.string().trim().defined(),
  classification_scheme: yup.string().trim().defined(),
  classification_outcome: yup.string().trim().defined(),
}).test(
  'authors-or-title',
  'Please provide at least a title or an author.',
  (values) => !!values.title?.trim() || !!values.authors?.trim(),
)

const { defineField, errors, handleSubmit, resetForm } = useForm<FormState>({
  validationSchema: schema,
  initialValues: emptyForm(),
})

const [authors] = defineField('authors')
const [title] = defineField('title')
const [doi] = defineField('doi')
const [restrictionsPriorToSampling] = defineField('restrictions_prior_to_sampling')
const [monitoredTransferFactors] = defineField('monitored_transfer_factors')
const [numberOfParticipants] = defineField('number_of_participants')
const [replicates] = defineField('replicates')
const [shedderTest] = defineField('shedder_test')
const [classificationCriteria] = defineField('classification_criteria')
const [classificationScheme] = defineField('classification_scheme')
const [classificationOutcome] = defineField('classification_outcome')

const showAddDialog = ref(false)
const saving = ref(false)
const saveError = ref('')

function openAddDialog() {
  resetForm({ values: emptyForm() })
  saveError.value = ''
  showAddDialog.value = true
}

const saveNewOption = handleSubmit(async (values) => {
  saving.value = true
  saveError.value = ''
  try {
    const created = await determinationOfSheddingPropensityCategoryApi.create({
      authors: values.authors.trim() || null,
      title: values.title.trim() || null,
      doi: values.doi.trim() || null,
      restrictions_prior_to_sampling: values.restrictions_prior_to_sampling.trim() || null,
      monitored_transfer_factors: values.monitored_transfer_factors.trim() || null,
      number_of_participants: values.number_of_participants.trim() || null,
      replicates: values.replicates.trim() || null,
      shedder_test: values.shedder_test.trim() || null,
      classification_criteria: values.classification_criteria.trim() || null,
      classification_scheme: values.classification_scheme.trim() || null,
      classification_outcome: values.classification_outcome.trim() || null,
    })
    options.value = [...options.value, created]
    modelValue.value = created.id
    showAddDialog.value = false
  } catch {
    saveError.value = 'Could not save this reference. Please try again.'
  } finally {
    saving.value = false
  }
})
</script>

<template>
  <div class="flex flex-col gap-2">
    <label class="font-medium text-sm">Determination of shedding propensity</label>
    <div class="flex gap-2">
      <Select
        v-model="modelValue"
        :options="selectOptions"
        option-label="label"
        option-value="id"
        placeholder="Select an option"
        :loading="loading"
        show-clear
        filter
        fluid
      />
      <Button icon="pi pi-plus" text aria-label="Add new reference" @click="openAddDialog" />
    </div>

    <Dialog
      v-model:visible="showAddDialog"
      header="Add determination of shedding propensity reference"
      modal
      :style="{ width: '36rem' }"
    >
      <div class="flex flex-col gap-4">
        <Message v-if="errors['']" severity="error" size="small" variant="simple">
          {{ errors[''] }}
        </Message>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Authors</label>
            <InputText v-model="authors" fluid autofocus />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Title</label>
            <InputText v-model="title" fluid />
          </div>
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">DOI (Optional)</label>
          <InputText v-model="doi" fluid />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Restrictions prior to sampling (Optional)</label>
          <Textarea v-model="restrictionsPriorToSampling" rows="2" fluid />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Monitored transfer factors (Optional)</label>
          <Textarea v-model="monitoredTransferFactors" rows="2" fluid />
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Number of participants (Optional)</label>
            <InputText v-model="numberOfParticipants" fluid />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Replicates (Optional)</label>
            <InputText v-model="replicates" fluid />
          </div>
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Shedder test (Optional)</label>
          <Textarea v-model="shedderTest" rows="2" fluid />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Classification criteria (Optional)</label>
          <Textarea v-model="classificationCriteria" rows="2" fluid />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Classification scheme (Optional)</label>
          <Textarea v-model="classificationScheme" rows="2" fluid />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Classification outcome (Optional)</label>
          <Textarea v-model="classificationOutcome" rows="2" fluid />
        </div>
        <p v-if="saveError" class="text-sm text-red-500">{{ saveError }}</p>
      </div>
      <template #footer>
        <Button label="Cancel" text @click="showAddDialog = false" />
        <Button label="Add" :loading="saving" @click="saveNewOption" />
      </template>
    </Dialog>
  </div>
</template>
