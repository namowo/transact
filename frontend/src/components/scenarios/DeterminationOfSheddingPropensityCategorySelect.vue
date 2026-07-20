<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Select from 'primevue/select'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
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

const showAddDialog = ref(false)
const saving = ref(false)
const saveError = ref('')

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

const form = ref<FormState>(emptyForm())

function openAddDialog() {
  form.value = emptyForm()
  saveError.value = ''
  showAddDialog.value = true
}

async function saveNewOption() {
  if (!form.value.title.trim() && !form.value.authors.trim()) return
  saving.value = true
  saveError.value = ''
  try {
    const created = await determinationOfSheddingPropensityCategoryApi.create({
      authors: form.value.authors.trim() || null,
      title: form.value.title.trim() || null,
      doi: form.value.doi.trim() || null,
      restrictions_prior_to_sampling: form.value.restrictions_prior_to_sampling.trim() || null,
      monitored_transfer_factors: form.value.monitored_transfer_factors.trim() || null,
      number_of_participants: form.value.number_of_participants.trim() || null,
      replicates: form.value.replicates.trim() || null,
      shedder_test: form.value.shedder_test.trim() || null,
      classification_criteria: form.value.classification_criteria.trim() || null,
      classification_scheme: form.value.classification_scheme.trim() || null,
      classification_outcome: form.value.classification_outcome.trim() || null,
    })
    options.value = [...options.value, created]
    modelValue.value = created.id
    showAddDialog.value = false
  } catch {
    saveError.value = 'Could not save this reference. Please try again.'
  } finally {
    saving.value = false
  }
}
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
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Authors</label>
            <InputText v-model="form.authors" fluid autofocus />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Title</label>
            <InputText v-model="form.title" fluid />
          </div>
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">DOI (Optional)</label>
          <InputText v-model="form.doi" fluid />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Restrictions prior to sampling (Optional)</label>
          <Textarea v-model="form.restrictions_prior_to_sampling" rows="2" fluid />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Monitored transfer factors (Optional)</label>
          <Textarea v-model="form.monitored_transfer_factors" rows="2" fluid />
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Number of participants (Optional)</label>
            <InputText v-model="form.number_of_participants" fluid />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Replicates (Optional)</label>
            <InputText v-model="form.replicates" fluid />
          </div>
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Shedder test (Optional)</label>
          <Textarea v-model="form.shedder_test" rows="2" fluid />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Classification criteria (Optional)</label>
          <Textarea v-model="form.classification_criteria" rows="2" fluid />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Classification scheme (Optional)</label>
          <Textarea v-model="form.classification_scheme" rows="2" fluid />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Classification outcome (Optional)</label>
          <Textarea v-model="form.classification_outcome" rows="2" fluid />
        </div>
        <p v-if="saveError" class="text-sm text-red-500">{{ saveError }}</p>
      </div>
      <template #footer>
        <Button label="Cancel" text @click="showAddDialog = false" />
        <Button
          label="Add"
          :loading="saving"
          :disabled="!form.title.trim() && !form.authors.trim()"
          @click="saveNewOption"
        />
      </template>
    </Dialog>
  </div>
</template>
