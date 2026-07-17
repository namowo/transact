<script setup lang="ts">
import { onMounted, ref } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import { createLaboratory, listLaboratories } from '@/api/laboratories'
import type { Laboratory } from '@/api/types'

const laboratories = ref<Laboratory[]>([])
const loading = ref(false)

const dialogVisible = ref(false)
const submitting = ref(false)
const submitError = ref('')
const form = ref({
  laboratory_name: '',
  institutional_affiliation: '',
  director_head_of_laboratory: '',
  street_address: '',
  postal_code: '',
  city: '',
  state: '',
  country: '',
  email: '',
})

async function load() {
  loading.value = true
  try {
    laboratories.value = await listLaboratories()
  } finally {
    loading.value = false
  }
}

onMounted(load)

function openDialog() {
  form.value = {
    laboratory_name: '',
    institutional_affiliation: '',
    director_head_of_laboratory: '',
    street_address: '',
    postal_code: '',
    city: '',
    state: '',
    country: '',
    email: '',
  }
  submitError.value = ''
  dialogVisible.value = true
}

async function submitNewLaboratory() {
  if (!form.value.laboratory_name.trim()) {
    submitError.value = 'Please enter a laboratory name.'
    return
  }
  submitting.value = true
  submitError.value = ''
  try {
    const created = await createLaboratory({
      ...form.value,
      laboratory_name: form.value.laboratory_name.trim(),
    })
    laboratories.value.push(created)
    dialogVisible.value = false
  } catch {
    submitError.value = 'Could not create the laboratory. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Laboratories</h1>
      <Button label="Add laboratory" icon="pi pi-plus" @click="openDialog" />
    </div>

    <div class="overflow-x-auto">
      <DataTable :value="laboratories" :loading="loading" data-key="id">
        <Column field="laboratory_name" header="Name" />
        <Column field="institutional_affiliation" header="Affiliation" />
        <Column field="city" header="City" />
        <Column field="country" header="Country" />
      </DataTable>
    </div>

    <Dialog
      v-model:visible="dialogVisible"
      header="Add laboratory"
      modal
      :style="{ width: '32rem' }"
    >
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label for="name" class="font-medium text-sm">Laboratory name *</label>
          <InputText id="name" v-model="form.laboratory_name" fluid autofocus />
        </div>
        <div class="flex flex-col gap-2">
          <label for="affiliation" class="font-medium text-sm">Institutional affiliation</label>
          <InputText id="affiliation" v-model="form.institutional_affiliation" fluid />
        </div>
        <div class="flex flex-col gap-2">
          <label for="director" class="font-medium text-sm">Director / head of laboratory</label>
          <InputText id="director" v-model="form.director_head_of_laboratory" fluid />
        </div>
        <div class="flex flex-col gap-2">
          <label for="street" class="font-medium text-sm">Street address</label>
          <InputText id="street" v-model="form.street_address" fluid />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div class="flex flex-col gap-2">
            <label for="postal" class="font-medium text-sm">Postal code</label>
            <InputText id="postal" v-model="form.postal_code" fluid />
          </div>
          <div class="flex flex-col gap-2">
            <label for="city" class="font-medium text-sm">City</label>
            <InputText id="city" v-model="form.city" fluid />
          </div>
          <div class="flex flex-col gap-2">
            <label for="state" class="font-medium text-sm">State</label>
            <InputText id="state" v-model="form.state" fluid />
          </div>
          <div class="flex flex-col gap-2">
            <label for="country" class="font-medium text-sm">Country</label>
            <InputText id="country" v-model="form.country" fluid />
          </div>
        </div>
        <div class="flex flex-col gap-2">
          <label for="lab-email" class="font-medium text-sm">Contact email</label>
          <InputText id="lab-email" v-model="form.email" type="email" fluid />
        </div>
        <Message v-if="submitError" severity="error" size="small">{{ submitError }}</Message>
      </div>
      <template #footer>
        <Button label="Cancel" text @click="dialogVisible = false" />
        <Button label="Add laboratory" :loading="submitting" @click="submitNewLaboratory" />
      </template>
    </Dialog>
  </div>
</template>
