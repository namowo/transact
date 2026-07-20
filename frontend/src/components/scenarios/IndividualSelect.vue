<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Select from 'primevue/select'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import SelectButton from 'primevue/selectbutton'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import SkinDiseaseCategorySelect from './SkinDiseaseCategorySelect.vue'
import DeterminationOfSheddingPropensityCategorySelect from './DeterminationOfSheddingPropensityCategorySelect.vue'
import { createIndividual, listIndividuals, updateIndividual } from '@/api/individuals'
import type { Individual } from '@/api/types'

// Selecting an individual here just picks which Individual row a surface
// points at; all of that person's editable fields (sex, age, ...) live in
// this component's dialog too, so they aren't duplicated in SurfaceForm.
const individualId = defineModel<number | null>({ default: null })

const sexOptions = [
  { label: 'm', value: 'm' },
  { label: 'f', value: 'f' },
  { label: 'd', value: 'd' },
]

const individuals = ref<Individual[]>([])
const loading = ref(false)

// Individuals have no name of their own, so label them by creation order
// (not their database id, which is an implementation detail) plus whatever
// traits are known, e.g. "Individual 3 (m, 34y)".
function describeIndividual(individual: Individual): string {
  const position = individuals.value.findIndex((candidate) => candidate.id === individual.id)
  const name = `Individual ${position + 1}`
  const parts = [individual.sex, individual.age != null ? `${individual.age}y` : null].filter(
    Boolean,
  )
  return parts.length ? `${name} (${parts.join(', ')})` : name
}

async function load() {
  loading.value = true
  try {
    individuals.value = (await listIndividuals()).sort((a, b) => a.id - b.id)
  } finally {
    loading.value = false
  }
}

onMounted(load)

const selectedIndividual = computed(
  () => individuals.value.find((candidate) => candidate.id === individualId.value) ?? null,
)

const showDialog = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const saving = ref(false)
const saveError = ref('')

const formSex = ref<string | null>(null)
const formAge = ref<number | null>(null)
const formDnaSheddingPropensity = ref<string | null>(null)
const formSkinDiseaseCategoryId = ref<number | null>(null)
const formDeterminationCategoryId = ref<number | null>(null)

function resetForm(individual: Individual | null) {
  formSex.value = individual?.sex ?? null
  formAge.value = individual?.age ?? null
  formDnaSheddingPropensity.value = individual?.dna_shedding_propensity ?? null
  formSkinDiseaseCategoryId.value = individual?.skin_disease_category_id ?? null
  formDeterminationCategoryId.value =
    individual?.determination_of_shedding_propensity_category_id ?? null
}

function openCreateDialog() {
  dialogMode.value = 'create'
  resetForm(null)
  saveError.value = ''
  showDialog.value = true
}

function openEditDialog() {
  if (!selectedIndividual.value) return
  dialogMode.value = 'edit'
  resetForm(selectedIndividual.value)
  saveError.value = ''
  showDialog.value = true
}

async function saveIndividual() {
  saving.value = true
  saveError.value = ''
  try {
    const payload = {
      sex: formSex.value,
      age: formAge.value,
      dna_shedding_propensity: formDnaSheddingPropensity.value,
      skin_disease_category_id: formSkinDiseaseCategoryId.value,
      determination_of_shedding_propensity_category_id: formDeterminationCategoryId.value,
    }
    if (dialogMode.value === 'edit' && selectedIndividual.value) {
      const updated = await updateIndividual(selectedIndividual.value.id, payload)
      individuals.value = individuals.value.map((candidate) =>
        candidate.id === updated.id ? updated : candidate,
      )
    } else {
      const created = await createIndividual(payload)
      individuals.value = [...individuals.value, created]
      individualId.value = created.id
    }
    showDialog.value = false
  } catch {
    saveError.value = 'Could not save this individual. Please try again.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-2">
    <label class="font-medium text-sm">Individual</label>
    <div class="flex gap-2">
      <Select
        v-model="individualId"
        :options="individuals"
        :option-label="describeIndividual"
        option-value="id"
        placeholder="Select an individual"
        :loading="loading"
        show-clear
        filter
        fluid
      />
      <Button
        v-if="selectedIndividual"
        icon="pi pi-pencil"
        text
        aria-label="Edit individual"
        @click="openEditDialog"
      />
      <Button icon="pi pi-plus" text aria-label="Add new individual" @click="openCreateDialog" />
    </div>

    <Dialog
      v-model:visible="showDialog"
      :header="dialogMode === 'edit' ? 'Edit individual' : 'Add individual'"
      modal
      :style="{ width: '28rem' }"
    >
      <div class="flex flex-col gap-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Sex (Optional)</label>
            <SelectButton
              v-model="formSex"
              :options="sexOptions"
              option-label="label"
              option-value="value"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Age (Optional)</label>
            <InputNumber v-model="formAge" fluid />
          </div>
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">DNA shedding propensity (Optional)</label>
          <InputText v-model="formDnaSheddingPropensity" fluid />
        </div>
        <SkinDiseaseCategorySelect v-model="formSkinDiseaseCategoryId" />
        <DeterminationOfSheddingPropensityCategorySelect v-model="formDeterminationCategoryId" />
        <p v-if="saveError" class="text-sm text-red-500">{{ saveError }}</p>
      </div>
      <template #footer>
        <Button label="Cancel" text @click="showDialog = false" />
        <Button label="Save" :loading="saving" @click="saveIndividual" />
      </template>
    </Dialog>
  </div>
</template>
