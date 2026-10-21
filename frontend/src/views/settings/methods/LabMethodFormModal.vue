<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import CategorySelect from '@/components/scenarios/CategorySelect.vue'
import DurationValueInput from '@/components/scenarios/DurationValueInput.vue'
import { getLabMethodConfig, type MethodFieldConfig } from '@/data/labMethods'
import { useAuthStore } from '@/stores/auth'

// Every lab-method field is optional at the API, so the schema built from
// `config.fields` only enforces the field's *type* (e.g. numbers must be
// numeric) - there's nothing to `required()` here.
function schemaForFields(fields: MethodFieldConfig[]) {
  const shape: Record<string, yup.AnySchema> = {}
  for (const field of fields) {
    switch (field.type) {
      case 'number':
      case 'duration':
        shape[field.key] = yup.number().nullable().defined()
        break
      case 'boolean':
        shape[field.key] = yup.boolean().defined()
        break
      default:
        shape[field.key] = yup.string().nullable().defined()
    }
  }
  return yup.object(shape)
}

const props = defineProps<{ methodKey: string; editingRow?: Record<string, unknown> | null }>()
const visible = defineModel<boolean>('visible', { required: true })

const emit = defineEmits<{ saved: [] }>()

const auth = useAuthStore()
const laboratoryId = computed(() => auth.user?.laboratory_id ?? null)

const config = computed(() => getLabMethodConfig(props.methodKey))
const editingId = computed(() => (props.editingRow ? String(props.editingRow.id) : null))

// eslint-disable-next-line @typescript-eslint/no-explicit-any -- form values are dynamic per method config
function emptyForm(fields: MethodFieldConfig[]): Record<string, any> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- form values are dynamic per method config
  const form: Record<string, any> = {}
  for (const field of fields) {
    form[field.key] = field.type === 'boolean' ? false : null
  }
  return form
}

const validationSchema = computed(() => schemaForFields(config.value?.fields ?? []))

// eslint-disable-next-line @typescript-eslint/no-explicit-any -- form values are dynamic per method config
const { errors, handleSubmit, resetForm, setFieldValue, values } = useForm<Record<string, any>>({
  validationSchema,
})

const submitting = ref(false)
const submitError = ref('')

watch(visible, (isVisible) => {
  if (!isVisible || !config.value) return
  submitError.value = ''
  if (props.editingRow) {
    const next = emptyForm(config.value.fields)
    for (const field of config.value.fields) {
      next[field.key] = (props.editingRow[field.key] as never) ?? (field.type === 'boolean' ? false : null)
    }
    resetForm({ values: next })
  } else {
    resetForm({ values: emptyForm(config.value.fields) })
  }
})

const submitForm = handleSubmit(async (formValues) => {
  if (!config.value) return
  submitting.value = true
  submitError.value = ''
  try {
    const payload = config.value.laboratoryScoped
      ? { ...formValues, laboratory_id: laboratoryId.value }
      : formValues
    if (editingId.value === null) {
      await config.value.api.create(payload)
    } else {
      await config.value.api.update(editingId.value, payload)
    }
    visible.value = false
    emit('saved')
  } catch {
    submitError.value = 'Could not save this entry. Please try again.'
  } finally {
    submitting.value = false
  }
})
</script>

<template>
  <UModal
    v-model:open="visible"
    :title="
      config
        ? editingId === null
          ? `Add ${config.label.toLowerCase()} entry`
          : `Edit ${config.label.toLowerCase()} entry`
        : ''
    "
    :ui="{ content: 'max-w-2xl', footer: 'justify-end' }"
  >
    <template #body>
      <form v-if="config" class="flex flex-col gap-4" @submit.prevent="submitForm">
        <div v-for="field in config.fields" :key="field.key" class="flex flex-col gap-2">
          <label v-if="field.type !== 'category'" class="font-medium text-sm">{{ field.label }}</label>

          <CategorySelect
            v-if="field.type === 'category'"
            :model-value="values[field.key]"
            :label="field.label"
            :api="field.categoryApi!"
            @update:model-value="setFieldValue(field.key, $event)"
          />

          <UFieldGroup v-else-if="field.type === 'number' && field.unit" class="w-full">
            <UInputNumber
              :model-value="values[field.key]"
              :color="errors[field.key] ? 'error' : undefined"
              orientation="vertical"
              class="w-full"
              @update:model-value="setFieldValue(field.key, $event)"
            />
            <UBadge color="neutral" variant="outline" size="lg" :label="field.unit" />
          </UFieldGroup>

          <UInputNumber
            v-else-if="field.type === 'number'"
            :model-value="values[field.key]"
            :color="errors[field.key] ? 'error' : undefined"
            orientation="vertical"
            class="w-full"
            @update:model-value="setFieldValue(field.key, $event)"
          />

          <DurationValueInput
            v-else-if="field.type === 'duration'"
            :model-value="values[field.key]"
            :invalid="!!errors[field.key]"
            @update:model-value="setFieldValue(field.key, $event)"
          />

          <div v-else-if="field.type === 'boolean'" class="flex items-center gap-2">
            <USwitch
              :model-value="values[field.key]"
              :id="field.key"
              @update:model-value="setFieldValue(field.key, $event)"
            />
          </div>

          <UTextarea
            v-else-if="field.type === 'textarea'"
            :model-value="values[field.key]"
            :rows="2"
            class="w-full"
            @update:model-value="setFieldValue(field.key, $event)"
          />

          <UInput
            v-else
            :model-value="values[field.key]"
            class="w-full"
            @update:model-value="setFieldValue(field.key, $event)"
          />
        </div>

        <UAlert v-if="submitError" color="error" variant="outline" :description="submitError" />
      </form>
    </template>

    <template #footer>
      <UButton
        label="Cancel"
        icon="i-lucide-x"
        variant="ghost"
        color="neutral"
        @click="visible = false"
      />
      <UButton
        :label="editingId === null ? 'Add entry' : 'Save changes'"
        icon="i-lucide-save"
        :loading="submitting"
        @click="submitForm"
      />
    </template>
  </UModal>
</template>
