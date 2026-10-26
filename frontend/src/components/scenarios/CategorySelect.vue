<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { useAuthStore } from '@/stores/auth'
import type { NamedCategory } from '@/api/types'

const props = withDefaults(
  defineProps<{
    label: string
    hint?: string
    description?: string
    api: {
      list: () => Promise<NamedCategory[]>
      create: (payload: {
        name?: string | null
        description?: string | null
      }) => Promise<NamedCategory>
      update?: (
        id: string,
        payload: { name?: string | null; description?: string | null },
      ) => Promise<NamedCategory>
    }
    placeholder?: string
    allowAdd?: boolean
    disabled?: boolean
    multiple?: boolean
  }>(),
  { allowAdd: true },
)

const modelValue = defineModel<string | string[] | null>({ default: null })

const auth = useAuthStore()
const canEdit = computed(() => auth.isLabAdmin && !!props.api.update)

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

// Edit button only ever targets a single option, so it's only offered for
// single-select usage - for multi-select, resolving "the" selected option
// to edit would be ambiguous.
const selectedOption = computed(() => {
  if (props.multiple || Array.isArray(modelValue.value)) return null
  return options.value.find((option) => option.id === modelValue.value) ?? null
})

async function onCreate(name: string) {
  const created = await props.api.create({ name })
  options.value = [...options.value, created]
  if (props.multiple) {
    const current = Array.isArray(modelValue.value) ? modelValue.value : []
    modelValue.value = [...current, created.id]
  } else {
    modelValue.value = created.id
  }
}

const schema = yup.object({
  name: yup.string().trim().required('Name is required.'),
})

const { defineField, errors, handleSubmit, resetForm } = useForm({
  validationSchema: schema,
  initialValues: { name: '' },
})

const [editName] = defineField('name')

const showEditDialog = ref(false)
const saving = ref(false)
const saveError = ref('')

function openEditDialog() {
  if (!selectedOption.value) return
  resetForm({ values: { name: selectedOption.value.name ?? '' } })
  saveError.value = ''
  showEditDialog.value = true
}

const saveEdit = handleSubmit(async (values) => {
  if (!selectedOption.value || !props.api.update) return
  saving.value = true
  saveError.value = ''
  try {
    const updated = await props.api.update(selectedOption.value.id, { name: values.name.trim() })
    options.value = options.value.map((option) => (option.id === updated.id ? updated : option))
    showEditDialog.value = false
  } catch {
    saveError.value = 'Could not save this option. Please try again.'
  } finally {
    saving.value = false
  }
})
</script>

<template>
  <UFormField :hint="hint" :ui="{ labelWrapper: 'flex-wrap' }">
    <template #label>
      <div class="flex items-start gap-1.5">
        <span class="whitespace-normal wrap-break-word">{{ label }}</span>
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
    </template>
    <div class="flex gap-2">
      <USelectMenu
        v-model="modelValue"
        :items="options"
        label-key="name"
        value-key="id"
        :multiple="multiple"
        :create-item="allowAdd"
        :placeholder="placeholder ?? 'Select an option'"
        :loading="loading"
        :disabled="disabled"
        clear
        class="w-full"
        :ui="{
          content: 'w-(--reka-combobox-trigger-width)',
          item: 'items-start',
          itemWrapper: 'min-w-0',
          itemLabel: 'whitespace-normal break-words',
        }"
        @create="onCreate"
      >
        <template #create-item-label="{ item }">
          <span class="flex items-center gap-2">
            <UIcon name="i-lucide-plus" class="text-sm" />
            Add "{{ item }}"
          </span>
        </template>
      </USelectMenu>
      <UButton
        v-if="canEdit && selectedOption"
        icon="i-lucide-pencil"
        variant="ghost"
        :disabled="disabled"
        aria-label="Edit selected option"
        @click="openEditDialog"
      />
    </div>

    <UModal
      v-model:open="showEditDialog"
      :title="`Edit ${label.toLowerCase()}`"
      :ui="{ content: 'max-w-md', footer: 'justify-end' }"
    >
      <template #body>
        <UFormField label="Name" :error="errors.name">
          <UInput v-model="editName" class="w-full" autofocus />
        </UFormField>
        <p v-if="saveError" class="text-sm text-red-500 mt-2">{{ saveError }}</p>
      </template>
      <template #footer>
        <UButton
          label="Cancel"
          icon="i-lucide-x"
          variant="ghost"
          @click="showEditDialog = false"
        />
        <UButton label="Save" icon="i-lucide-save" :loading="saving" @click="saveEdit" />
      </template>
    </UModal>
  </UFormField>
</template>
