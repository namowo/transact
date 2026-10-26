<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { onKeyStroke } from '@vueuse/core'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import CategorySelect from '@/components/scenarios/CategorySelect.vue'
import DurationValueInput from '@/components/scenarios/DurationValueInput.vue'
import { getLabMethodConfig, type MethodFieldConfig } from '@/data/labMethods'
import { samplingMethodApi } from '@/api/methods'
import { useAuthStore } from '@/stores/auth'
import type { SamplingMethod } from '@/api/types'

// Every sub-method field is optional at the API (a tab left blank is simply
// skipped on submit), so the schema only enforces each field's type.
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

const props = defineProps<{
  editingRow?: SamplingMethod | null
  // Pre-fills a new (not editing) entry with another row's values, for the
  // "Duplicate" action - unlike editingRow, the sub-methods are created
  // fresh rather than updating the source's records.
  duplicateFrom?: SamplingMethod | null
}>()
const visible = defineModel<boolean>('visible', { required: true })

const emit = defineEmits<{ saved: [] }>()

// :dismissible="false" blocks both outside-click and Escape at the Reka UI
// level (to stop outside clicks from silently discarding the form) - Escape
// is wired back up separately so it still closes the modal.
onKeyStroke('Escape', () => {
  if (visible.value) visible.value = false
})

const auth = useAuthStore()
const laboratoryId = computed(() => auth.user?.laboratory_id ?? null)

const editingId = computed(() => props.editingRow?.id ?? null)

const subMethodKeys = ['swab', 'tape', 'vacuum', 'cutting', 'scraping', 'picking'] as const
type SubMethodKey = (typeof subMethodKeys)[number]

const subMethodConfigs = subMethodKeys.map((key) => getLabMethodConfig(key)!)

// eslint-disable-next-line @typescript-eslint/no-explicit-any -- form values are dynamic per method config
function emptyForm(fields: MethodFieldConfig[]): Record<string, any> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- form values are dynamic per method config
  const form: Record<string, any> = {}
  for (const field of fields) {
    form[field.key] = field.type === 'boolean' ? false : null
  }
  return form
}

// One independent vee-validate form per sub-method tab - each tab is
// optional and self-contained, so there's no shared parent schema.
const subForms = Object.fromEntries(
  subMethodConfigs.map((config) => [
    config.key,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- form values are dynamic per method config
    useForm<Record<string, any>>({
      validationSchema: schemaForFields(config.fields),
      initialValues: emptyForm(config.fields),
    }),
  ]),
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- form values are dynamic per method config
) as Record<SubMethodKey, ReturnType<typeof useForm<Record<string, any>>>>

// eslint-disable-next-line @typescript-eslint/no-explicit-any -- form values are dynamic per method config
function formValues(key: SubMethodKey): Record<string, any> {
  return subForms[key].values
}

function fieldValue(key: SubMethodKey, fieldKey: string) {
  return subForms[key].values[fieldKey]
}

function setFieldValue(key: SubMethodKey, fieldKey: string, value: unknown) {
  subForms[key].setFieldValue(fieldKey, value)
}

function fieldError(key: SubMethodKey, fieldKey: string) {
  return subForms[key].errors.value[fieldKey]
}

// Existing sub-method record ids, so editing updates them instead of
// creating duplicates.
const existingSubMethodIds = ref<Record<SubMethodKey, string | null>>(
  Object.fromEntries(subMethodKeys.map((key) => [key, null])) as Record<
    SubMethodKey,
    string | null
  >,
)

const submitting = ref(false)
const submitError = ref('')

watch(visible, (isVisible) => {
  if (!isVisible) return
  submitError.value = ''
  const source = props.editingRow ?? props.duplicateFrom
  for (const config of subMethodConfigs) {
    const key = config.key as SubMethodKey
    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- sub-method field is dynamic per key
    const subMethod = source ? (source as any)[`${key}_method`] : null
    // Duplicating must create new sub-method records, not overwrite the
    // source's - only track an existing id when actually editing.
    existingSubMethodIds.value[key] = props.editingRow ? subMethod?.id ?? null : null
    if (subMethod) {
      const next = emptyForm(config.fields)
      for (const field of config.fields) {
        next[field.key] = subMethod[field.key] ?? (field.type === 'boolean' ? false : null)
      }
      subForms[key].resetForm({ values: next })
    } else {
      subForms[key].resetForm({ values: emptyForm(config.fields) })
    }
  }
})

// A sub-method tab is only saved if the user filled in at least one field.
// eslint-disable-next-line @typescript-eslint/no-explicit-any -- form values are dynamic per method config
function isFormEmpty(form: Record<string, any>): boolean {
  return Object.values(form).every((value) => value === null || value === false || value === '')
}

async function onSubmit() {
  submitting.value = true
  submitError.value = ''
  try {
    // Validate every non-empty tab before saving anything - a blank tab is
    // skipped, but a partially-filled one must pass its schema.
    for (const config of subMethodConfigs) {
      const key = config.key as SubMethodKey
      if (isFormEmpty(formValues(key))) continue
      const { valid } = await subForms[key].validate()
      if (!valid) {
        submitError.value = 'Please fix the highlighted fields before saving.'
        submitting.value = false
        return
      }
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any -- built up incrementally below
    const subMethodIds: Record<SubMethodKey, string | null> = {} as any

    for (const config of subMethodConfigs) {
      const key = config.key as SubMethodKey
      const form = formValues(key)
      const existingId = existingSubMethodIds.value[key]

      if (isFormEmpty(form)) {
        subMethodIds[key] = existingId
        continue
      }

      const saved = existingId
        ? await config.api.update(existingId, form)
        : await config.api.create(form)
      subMethodIds[key] = saved.id
    }

    const payload = {
      laboratory_id: laboratoryId.value,
      swab_method_id: subMethodIds.swab,
      tape_method_id: subMethodIds.tape,
      vacuum_method_id: subMethodIds.vacuum,
      cutting_method_id: subMethodIds.cutting,
      scraping_method_id: subMethodIds.scraping,
      picking_method_id: subMethodIds.picking,
    }

    if (editingId.value === null) {
      await samplingMethodApi.create(payload)
    } else {
      await samplingMethodApi.update(editingId.value, payload)
    }

    visible.value = false
    emit('saved')
  } catch {
    submitError.value = 'Could not save this sampling method. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <UModal
    v-model:open="visible"
    :title="editingId === null ? 'Add sampling method' : 'Edit sampling method'"
    :dismissible="false"
    :ui="{ content: 'max-w-3xl', footer: 'justify-end' }"
  >
    <template #body>
      <form class="flex flex-col gap-4" @submit.prevent="onSubmit">
        <p class="text-sm text-surface-500 dark:text-surface-400">
          Fill in the sub-methods that are relevant for this sampling method. Tabs left empty are
          skipped.
        </p>

        <UTabs default-value="swab" :items="subMethodConfigs" value-key="key" class="w-full">
          <template #content="{ item: config }">
            <div class="flex flex-col gap-4">
              <div v-for="field in config.fields" :key="field.key" class="flex flex-col gap-2">
                <label v-if="field.type !== 'category'" class="font-medium text-sm">{{ field.label }}</label>

                <CategorySelect
                  v-if="field.type === 'category'"
                  :model-value="fieldValue(config.key as typeof subMethodKeys[number], field.key)"
                  :label="field.label"
                  :api="field.categoryApi!"
                  @update:model-value="
                    setFieldValue(config.key as typeof subMethodKeys[number], field.key, $event)
                  "
                />

                <UFieldGroup v-else-if="field.type === 'number' && field.unit" class="w-full">
                  <UInputNumber
                    :model-value="fieldValue(config.key as typeof subMethodKeys[number], field.key)"
                    :color="fieldError(config.key as typeof subMethodKeys[number], field.key) ? 'error' : undefined"
                    orientation="vertical"
                    class="w-full"
                    @update:model-value="
                      setFieldValue(config.key as typeof subMethodKeys[number], field.key, $event)
                    "
                  />
                  <UBadge color="neutral" variant="outline" size="lg" :label="field.unit" />
                </UFieldGroup>

                <UInputNumber
                  v-else-if="field.type === 'number'"
                  :model-value="fieldValue(config.key as typeof subMethodKeys[number], field.key)"
                  :color="fieldError(config.key as typeof subMethodKeys[number], field.key) ? 'error' : undefined"
                  orientation="vertical"
                  class="w-full"
                  @update:model-value="
                    setFieldValue(config.key as typeof subMethodKeys[number], field.key, $event)
                  "
                />

                <DurationValueInput
                  v-else-if="field.type === 'duration'"
                  :model-value="fieldValue(config.key as typeof subMethodKeys[number], field.key)"
                  :invalid="!!fieldError(config.key as typeof subMethodKeys[number], field.key)"
                  @update:model-value="
                    setFieldValue(config.key as typeof subMethodKeys[number], field.key, $event)
                  "
                />

                <div v-else-if="field.type === 'boolean'" class="flex items-center gap-2">
                  <USwitch
                    :model-value="fieldValue(config.key as typeof subMethodKeys[number], field.key)"
                    :id="`${config.key}-${field.key}`"
                    @update:model-value="
                      setFieldValue(config.key as typeof subMethodKeys[number], field.key, $event)
                    "
                  />
                </div>

                <UTextarea
                  v-else-if="field.type === 'textarea'"
                  :model-value="fieldValue(config.key as typeof subMethodKeys[number], field.key)"
                  :rows="2"
                  class="w-full"
                  @update:model-value="
                    setFieldValue(config.key as typeof subMethodKeys[number], field.key, $event)
                  "
                />

                <USelect
                  v-else-if="field.type === 'select'"
                  :model-value="fieldValue(config.key as typeof subMethodKeys[number], field.key)"
                  :items="field.options"
                  class="w-full"
                  @update:model-value="
                    setFieldValue(config.key as typeof subMethodKeys[number], field.key, $event)
                  "
                />

                <UInput
                  v-else
                  :model-value="fieldValue(config.key as typeof subMethodKeys[number], field.key)"
                  class="w-full"
                  @update:model-value="
                    setFieldValue(config.key as typeof subMethodKeys[number], field.key, $event)
                  "
                />

                <UAlert
                  v-if="fieldError(config.key as typeof subMethodKeys[number], field.key)"
                  color="error"
                  variant="subtle"
                  :description="fieldError(config.key as typeof subMethodKeys[number], field.key)"
                />
              </div>
            </div>
          </template>
        </UTabs>

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
        :label="editingId === null ? 'Add sampling method' : 'Save changes'"
        icon="i-lucide-save"
        :loading="submitting"
        @click="onSubmit"
      />
    </template>
  </UModal>
</template>
