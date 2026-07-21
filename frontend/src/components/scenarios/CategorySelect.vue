<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import Select from 'primevue/select'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Message from 'primevue/message'
import type { NamedCategory } from '@/api/types'

const props = defineProps<{
  modelValue: number | null
  label: string
  api: {
    list: () => Promise<NamedCategory[]>
    create: (payload: {
      name?: string | null
      description?: string | null
    }) => Promise<NamedCategory>
  }
  placeholder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number | null]
}>()

const options = ref<NamedCategory[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    options.value = await props.api.list()
  } finally {
    loading.value = false
  }
}

onMounted(load)

const schema = yup.object({
  name: yup.string().trim().required('Name is required.'),
  description: yup.string().trim().defined(),
})

const { defineField, errors, handleSubmit, resetForm } = useForm({
  validationSchema: schema,
  initialValues: { name: '', description: '' },
})

const [newName] = defineField('name')
const [newDescription] = defineField('description')

const showAddDialog = ref(false)
const saving = ref(false)
const saveError = ref('')

function openAddDialog() {
  resetForm({ values: { name: '', description: '' } })
  saveError.value = ''
  showAddDialog.value = true
}

const saveNewOption = handleSubmit(async (values) => {
  saving.value = true
  saveError.value = ''
  try {
    const created = await props.api.create({
      name: values.name.trim(),
      description: values.description.trim() || null,
    })
    options.value = [...options.value, created]
    emit('update:modelValue', created.id)
    showAddDialog.value = false
  } catch {
    saveError.value = 'Could not save this option. Please try again.'
  } finally {
    saving.value = false
  }
})
</script>

<template>
  <div class="flex flex-col gap-2">
    <label class="font-medium text-sm">{{ label }}</label>
    <div class="flex gap-2">
      <Select
        :model-value="modelValue"
        :options="options"
        option-label="name"
        option-value="id"
        :placeholder="placeholder ?? 'Select an option'"
        :loading="loading"
        show-clear
        filter
        fluid
        @update:model-value="emit('update:modelValue', $event)"
      />
      <Button icon="pi pi-plus" text aria-label="Add new option" @click="openAddDialog" />
    </div>

    <Dialog
      v-model:visible="showAddDialog"
      :header="`Add ${label}`"
      modal
      :style="{ width: '28rem' }"
    >
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Name</label>
          <InputText v-model="newName" :invalid="!!errors.name" fluid autofocus />
          <Message v-if="errors.name" severity="error" size="small" variant="simple">
            {{ errors.name }}
          </Message>
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Description (Optional)</label>
          <Textarea v-model="newDescription" rows="2" fluid />
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
