<script setup lang="ts">
import { onMounted, ref } from 'vue'
import Select from 'primevue/select'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import { skinDiseaseCategoryApi } from '@/api/categories'
import type { SkinDiseaseCategory } from '@/api/types'

const modelValue = defineModel<number | null>({ default: null })

const options = ref<SkinDiseaseCategory[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    options.value = await skinDiseaseCategoryApi.list()
  } finally {
    loading.value = false
  }
}

onMounted(load)

const showAddDialog = ref(false)
const newName = ref('')
const newInfluence = ref(false)
const newLiterature = ref('')
const saving = ref(false)
const saveError = ref('')

function openAddDialog() {
  newName.value = ''
  newInfluence.value = false
  newLiterature.value = ''
  saveError.value = ''
  showAddDialog.value = true
}

async function saveNewOption() {
  if (!newName.value.trim()) return
  saving.value = true
  saveError.value = ''
  try {
    const created = await skinDiseaseCategoryApi.create({
      name: newName.value.trim(),
      influence_on_shedding_propensity: newInfluence.value,
      literature: newLiterature.value.trim() || null,
    })
    options.value = [...options.value, created]
    modelValue.value = created.id
    showAddDialog.value = false
  } catch {
    saveError.value = 'Could not save this option. Please try again.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-2">
    <label class="font-medium text-sm">Skin disease category</label>
    <div class="flex gap-2">
      <Select
        v-model="modelValue"
        :options="options"
        option-label="name"
        option-value="id"
        placeholder="Select an option"
        :loading="loading"
        show-clear
        filter
        fluid
      />
      <Button icon="pi pi-plus" text aria-label="Add new option" @click="openAddDialog" />
    </div>

    <Dialog
      v-model:visible="showAddDialog"
      header="Add skin disease category"
      modal
      :style="{ width: '28rem' }"
    >
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Name</label>
          <InputText v-model="newName" fluid autofocus />
        </div>
        <div class="flex items-center gap-2">
          <ToggleSwitch v-model="newInfluence" input-id="influence-shedding" />
          <label for="influence-shedding" class="text-sm">Influences shedding propensity</label>
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Literature (Optional)</label>
          <Textarea v-model="newLiterature" rows="2" fluid />
        </div>
        <p v-if="saveError" class="text-sm text-red-500">{{ saveError }}</p>
      </div>
      <template #footer>
        <Button label="Cancel" text @click="showAddDialog = false" />
        <Button label="Add" :loading="saving" :disabled="!newName.trim()" @click="saveNewOption" />
      </template>
    </Dialog>
  </div>
</template>
