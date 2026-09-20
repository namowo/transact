<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { skinDiseaseCategoryApi } from '@/api/categories'
import type { SkinDiseaseCategory } from '@/api/types'

const modelValue = defineModel<string | null>({ default: null })

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

const schema = yup.object({
  name: yup.string().trim().required('Name is required.'),
  influence: yup.boolean().defined(),
  literature: yup.string().trim().defined(),
})

const { defineField, errors, handleSubmit, resetForm } = useForm({
  validationSchema: schema,
  initialValues: { name: '', influence: false, literature: '' },
})

const [newName] = defineField('name')
const [newInfluence] = defineField('influence')
const [newLiterature] = defineField('literature')

const showAddDialog = ref(false)
const saving = ref(false)
const saveError = ref('')

function openAddDialog() {
  resetForm({ values: { name: '', influence: false, literature: '' } })
  saveError.value = ''
  showAddDialog.value = true
}

const saveNewOption = handleSubmit(async (values) => {
  saving.value = true
  saveError.value = ''
  try {
    const created = await skinDiseaseCategoryApi.create({
      name: values.name.trim(),
      influence_on_shedding_propensity: values.influence,
      literature: values.literature.trim() || null,
    })
    options.value = [...options.value, created]
    modelValue.value = created.id
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
    <label class="font-medium text-sm">Skin disease category</label>
    <div class="flex gap-2">
      <USelectMenu
        v-model="modelValue"
        :items="options"
        label-key="name"
        value-key="id"
        placeholder="Select an option"
        :loading="loading"
        clear
        class="w-full"
      />
      <UButton icon="i-lucide-plus" variant="ghost" aria-label="Add new option" @click="openAddDialog" />
    </div>

    <UModal
      v-model:open="showAddDialog"
      title="Add skin disease category"
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
          <UAlert v-if="errors.name" color="error" variant="subtle" :description="errors.name" />
        </div>
        <div class="flex items-center gap-2">
          <USwitch v-model="newInfluence" id="influence-shedding" />
          <label for="influence-shedding" class="text-sm">Influences shedding propensity</label>
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Literature (Optional)</label>
          <UTextarea v-model="newLiterature" :rows="2" class="w-full" />
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
