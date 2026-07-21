<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import Button from 'primevue/button'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import CategorySelect from '@/components/scenarios/CategorySelect.vue'
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

const props = defineProps<{ methodKey: string; id?: string }>()

const router = useRouter()
const auth = useAuthStore()
const laboratoryId = computed(() => auth.user?.laboratory_id ?? null)

const config = computed(() => getLabMethodConfig(props.methodKey))
const editingId = computed(() => (props.id ? Number(props.id) : null))

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

const loading = ref(false)
const loadError = ref('')
const submitting = ref(false)
const submitError = ref('')

onMounted(async () => {
  if (!config.value) return
  resetForm({ values: emptyForm(config.value.fields) })
  if (editingId.value === null) return
  loading.value = true
  loadError.value = ''
  try {
    const all = await config.value.api.list()
    const row = all.find((item) => item.id === editingId.value)
    if (!row) {
      loadError.value = 'This entry could not be found.'
      return
    }
    const next = emptyForm(config.value.fields)
    for (const field of config.value.fields) {
      next[field.key] = row[field.key] ?? (field.type === 'boolean' ? false : null)
    }
    resetForm({ values: next })
  } catch {
    loadError.value = 'Could not load this entry.'
  } finally {
    loading.value = false
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
    router.push({ name: `settings-methods-${config.value.key}` })
  } catch {
    submitError.value = 'Could not save this entry. Please try again.'
  } finally {
    submitting.value = false
  }
})

function onCancel() {
  if (!config.value) return
  router.push({ name: `settings-methods-${config.value.key}` })
}
</script>

<template>
  <div v-if="config" class="flex flex-col gap-6 max-w-3xl">
    <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">
      {{ editingId === null ? `Add ${config.label.toLowerCase()} entry` : `Edit ${config.label.toLowerCase()} entry` }}
    </h1>

    <div v-if="loading" class="flex justify-center py-12">
      <ProgressSpinner style="width: 3rem; height: 3rem" />
    </div>

    <Message v-else-if="loadError" severity="error" size="small">{{ loadError }}</Message>

    <form v-else class="flex flex-col gap-4" @submit.prevent="submitForm">
      <div v-for="field in config.fields" :key="field.key" class="flex flex-col gap-2">
        <label v-if="field.type !== 'category'" class="font-medium text-sm">{{ field.label }}</label>

        <CategorySelect
          v-if="field.type === 'category'"
          :model-value="values[field.key]"
          :label="field.label"
          :api="field.categoryApi!"
          @update:model-value="setFieldValue(field.key, $event)"
        />

        <InputNumber
          v-else-if="field.type === 'number'"
          :model-value="values[field.key]"
          :invalid="!!errors[field.key]"
          fluid
          @update:model-value="setFieldValue(field.key, $event)"
        />

        <div v-else-if="field.type === 'boolean'" class="flex items-center gap-2">
          <ToggleSwitch
            :model-value="values[field.key]"
            :input-id="field.key"
            @update:model-value="setFieldValue(field.key, $event)"
          />
        </div>

        <Textarea
          v-else-if="field.type === 'textarea'"
          :model-value="values[field.key]"
          rows="2"
          fluid
          @update:model-value="setFieldValue(field.key, $event)"
        />

        <InputText
          v-else
          :model-value="values[field.key]"
          fluid
          @update:model-value="setFieldValue(field.key, $event)"
        />
      </div>

      <Message v-if="submitError" severity="error" size="small">{{ submitError }}</Message>

      <div class="flex gap-2 mt-2">
        <Button
          type="submit"
          :label="editingId === null ? `Add ${config.label.toLowerCase()} entry` : 'Save changes'"
          :loading="submitting"
        />
        <Button label="Cancel" text type="button" @click="onCancel" />
      </div>
    </form>
  </div>
</template>
