<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import type { NamedCategory } from '@/api/types'

const props = defineProps<{
  modelValue: string | null
  label: string
  description?: string
  api: {
    list: () => Promise<NamedCategory[]>
    create: (payload: {
      name?: string | null
      description?: string | null
    }) => Promise<NamedCategory>
  }
  placeholder?: string
  allowAdd?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string | null]
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
    <div class="flex items-center gap-1.5">
      <label class="font-medium text-sm">{{ label }}</label>
      <UTooltip
        v-if="description"
        :text="description"
        :content="{ side: 'top' }"
        :ui="{ content: 'max-w-xs' }"
      >
        <UIcon
          name="i-lucide-info"
          class="text-surface-500 dark:text-surface-400 text-sm cursor-help"
        />
      </UTooltip>
    </div>
    <div class="flex gap-2">
      <USelectMenu
        :model-value="modelValue"
        :items="options"
        label-key="name"
        value-key="id"
        :placeholder="placeholder ?? 'Select an option'"
        :loading="loading"
        clear
        class="w-full"
        @update:model-value="emit('update:modelValue', $event)"
      />
      <UButton
        v-if="allowAdd ?? true"
        icon="i-lucide-plus"
        variant="ghost"
        aria-label="Add new option"
        @click="openAddDialog"
      />
    </div>

    <UModal
      v-model:open="showAddDialog"
      :title="`Add ${label}`"
      :ui="{ content: 'max-w-md' }"
    >
      <template #body>
        <div class="flex flex-col gap-4">
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Name</label>
            <UInput
              v-model="newName"
              :color="errors.name ? 'error' : undefined"
              class="w-full"
              autofocus
            />
            <UAlert
              v-if="errors.name"
              color="error"
              variant="subtle"
              :description="errors.name"
            />
          </div>
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Description (Optional)</label>
            <UTextarea v-model="newDescription" rows="2" class="w-full" />
          </div>
          <p v-if="saveError" class="text-sm text-red-500">{{ saveError }}</p>
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" variant="ghost" @click="showAddDialog = false" />
        <UButton label="Add" :loading="saving" @click="saveNewOption" />
      </template>
    </UModal>
  </div>
</template>
