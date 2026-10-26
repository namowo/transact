<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { onKeyStroke } from '@vueuse/core'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import CategorySelect from '@/components/scenarios/CategorySelect.vue'
import EntitySelect from '@/components/scenarios/EntitySelect.vue'
import MultiCategorySelect from '@/components/scenarios/MultiCategorySelect.vue'
import CheckboxGroupSelect from '@/components/scenarios/CheckboxGroupSelect.vue'
import DurationValueInput from '@/components/scenarios/DurationValueInput.vue'
import { getLabMethodConfig, type MethodFieldConfig } from '@/data/labMethods'
import { useAuthStore } from '@/stores/auth'

let nextRowId = 0

// Each row gets a stable `_rowId`, independent of its position in the
// array, so the `v-for` below can key on it instead of the array index -
// keying by index made Vue reuse a row's DOM/component instance for
// whatever row shifted into that slot after a deletion, instead of
// removing the instance the user actually clicked delete on. `_rowId` is
// stripped before submit.
// eslint-disable-next-line @typescript-eslint/no-explicit-any -- form values are dynamic per method config
function emptyRow(rowFields: MethodFieldConfig[]): Record<string, any> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- form values are dynamic per method config
  const row: Record<string, any> = { _rowId: nextRowId++ }
  for (const field of rowFields) {
    row[field.key] = field.type === 'boolean' ? false : null
  }
  return row
}

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
      case 'repeatable-group':
        // Rows aren't individually validated - each row is just a
        // component + volume pair, both optional.
        shape[field.key] = yup.array().defined()
        break
      case 'multi-select':
      case 'checkbox-group':
        shape[field.key] = yup.array().of(yup.string().defined()).defined()
        break
      case 'entity-select':
        shape[field.key] = yup.string().nullable().defined()
        break
      default:
        shape[field.key] = yup.string().nullable().defined()
    }
  }
  return yup.object(shape)
}

const props = defineProps<{
  methodKey: string
  editingRow?: Record<string, unknown> | null
  // Pre-fills a new (not editing) entry with another row's values, for the
  // "Duplicate" action - distinct from `editingRow` so the save still
  // creates a new record instead of overwriting the source one.
  duplicateFrom?: Record<string, unknown> | null
}>()
const visible = defineModel<boolean>('visible', { required: true })

const emit = defineEmits<{ saved: [] }>()

const auth = useAuthStore()
const laboratoryId = computed(() => auth.user?.laboratory_id ?? null)

const config = computed(() => getLabMethodConfig(props.methodKey))
const editingId = computed(() => (props.editingRow ? String(props.editingRow.id) : null))

// :dismissible="false" blocks both outside-click and Escape at the Reka UI
// level (to stop outside clicks from silently discarding the form) - Escape
// is wired back up separately so it still closes the modal.
onKeyStroke('Escape', () => {
  if (visible.value) visible.value = false
})

// eslint-disable-next-line @typescript-eslint/no-explicit-any -- form values are dynamic per method config
function emptyForm(fields: MethodFieldConfig[]): Record<string, any> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- form values are dynamic per method config
  const form: Record<string, any> = {}
  for (const field of fields) {
    form[field.key] =
      field.type === 'boolean'
        ? false
        : field.type === 'repeatable-group'
          // Always start with one row so the user sees the fields to fill in
          // rather than an empty section with just an "add" button.
          ? [emptyRow(field.rowFields ?? [])]
          : field.type === 'multi-select' || field.type === 'checkbox-group'
            ? []
            : null
  }
  return form
}

const validationSchema = computed(() => schemaForFields(config.value?.fields ?? []))

// eslint-disable-next-line @typescript-eslint/no-explicit-any -- entity shape varies per field
const entityOptions = ref<Record<string, any[]>>({})

async function loadEntityOptions() {
  for (const field of config.value?.fields ?? []) {
    if (field.type !== 'entity-select' || !field.entityApi) continue
    entityOptions.value[field.key] = await field.entityApi.list()
  }
}

onMounted(loadEntityOptions)
watch(() => props.methodKey, loadEntityOptions)

// eslint-disable-next-line @typescript-eslint/no-explicit-any -- form values are dynamic per method config
const { errors, handleSubmit, resetForm, setFieldValue, values } = useForm<Record<string, any>>({
  validationSchema,
})

const submitting = ref(false)
const submitError = ref('')

function visibleFields() {
  return (config.value?.fields ?? []).filter((field) => !field.visibleWhen || field.visibleWhen(values))
}

// Keep derived fields (e.g. a volume that's the sum of other volumes) in
// sync with their dependencies, so the stored value always matches what's
// shown - it's saved as a "double check" value, not purely cosmetic.
watch(
  values,
  () => {
    for (const field of config.value?.fields ?? []) {
      if (!field.computed) continue
      const next = field.computed(values)
      if (values[field.key] !== next) setFieldValue(field.key, next)
    }
  },
  { deep: true },
)

watch(visible, (isVisible) => {
  if (!isVisible || !config.value) return
  submitError.value = ''
  const source = props.editingRow ?? props.duplicateFrom
  if (source) {
    const next = emptyForm(config.value.fields)
    for (const field of config.value.fields) {
      if (field.type === 'repeatable-group') {
        const rows = (source[field.key] as Record<string, unknown>[] | undefined) ?? []
        const mapped = rows.map((row) => {
          const value = emptyRow(field.rowFields ?? [])
          for (const rowField of field.rowFields ?? []) {
            value[rowField.key] = row[rowField.key] ?? null
          }
          return value
        })
        next[field.key] = mapped.length ? mapped : [emptyRow(field.rowFields ?? [])]
        continue
      }
      if (field.type === 'multi-select' || field.type === 'checkbox-group') {
        const items = (source[field.sourceKey ?? field.key] as { id: string }[] | undefined) ?? []
        next[field.key] = items.map((item) => item.id)
        continue
      }
      next[field.key] = (source[field.key] as never) ?? (field.type === 'boolean' ? false : null)
    }
    resetForm({ values: next })
  } else {
    resetForm({ values: emptyForm(config.value.fields) })
  }
})

function addRow(field: MethodFieldConfig) {
  setFieldValue(field.key, [...(values[field.key] ?? []), emptyRow(field.rowFields ?? [])])
}

function removeRow(field: MethodFieldConfig, index: number) {
  setFieldValue(
    field.key,
    (values[field.key] ?? []).filter((_: unknown, i: number) => i !== index),
  )
}

function setRowValue(field: MethodFieldConfig, index: number, rowFieldKey: string, value: unknown) {
  const rows = [...(values[field.key] ?? [])]
  rows[index] = { ...rows[index], [rowFieldKey]: value }
  setFieldValue(field.key, rows)
}

const submitForm = handleSubmit(async (formValues) => {
  if (!config.value) return
  submitting.value = true
  submitError.value = ''
  try {
    const cleaned = { ...formValues }
    for (const field of config.value.fields) {
      if (field.type !== 'repeatable-group') continue
      cleaned[field.key] = (cleaned[field.key] ?? [])
        // Drop rows left completely blank (e.g. the row shown by default).
        .filter((row: Record<string, unknown>) =>
          (field.rowFields ?? []).some((rowField) => row[rowField.key] !== null && row[rowField.key] !== ''),
        )
        // `_rowId` is a local-only key for stable `v-for` identity, not API data.
        .map(({ _rowId, ...row }: Record<string, unknown>) => row)
    }
    const payload = config.value.laboratoryScoped
      ? { ...cleaned, laboratory_id: laboratoryId.value }
      : cleaned
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
          ? `Add ${config.entryLabel ?? `${config.label.toLowerCase()} entry`}`
          : `Edit ${config.entryLabel ?? `${config.label.toLowerCase()} entry`}`
        : ''
    "
    :dismissible="false"
    :ui="{ content: 'max-w-2xl', footer: 'justify-end' }"
  >
    <template #body>
      <form v-if="config" class="flex flex-col gap-4" @submit.prevent="submitForm">
        <div v-for="field in visibleFields()" :key="field.key" class="flex flex-col gap-2">
          <div
            v-if="
              field.type !== 'category' &&
              field.type !== 'entity-select' &&
              field.type !== 'repeatable-group' &&
              field.type !== 'multi-select' &&
              field.type !== 'checkbox-group'
            "
            class="flex items-start justify-between gap-1.5"
          >
            <div class="flex items-start gap-1.5">
              <label :for="field.type === 'boolean' ? field.key : undefined" class="font-medium text-sm">{{
                field.label
              }}</label>
              <UTooltip
                v-if="field.hint"
                :text="field.hint"
                :content="{ side: 'top' }"
                :ui="{ content: 'max-w-xs' }"
              >
                <UIcon
                  name="i-lucide-info"
                  class="text-surface-500 dark:text-surface-400 text-sm cursor-help"
                />
              </UTooltip>
            </div>

            <USwitch
              v-if="field.type === 'boolean'"
              :model-value="values[field.key]"
              :id="field.key"
              @update:model-value="setFieldValue(field.key, $event)"
            />
          </div>

          <CategorySelect
            v-if="field.type === 'category'"
            :model-value="values[field.key]"
            :label="field.label"
            :description="field.hint"
            :api="field.categoryApi!"
            @update:model-value="setFieldValue(field.key, $event)"
          />

          <EntitySelect
            v-else-if="field.type === 'entity-select'"
            :model-value="values[field.key]"
            :label="field.label"
            :options="entityOptions[field.key] ?? []"
            :option-label="field.entityLabel ?? ((entity) => entity?.id ?? '')"
            @update:model-value="setFieldValue(field.key, $event)"
          />

          <MultiCategorySelect
            v-else-if="field.type === 'multi-select'"
            :model-value="values[field.key]"
            :label="field.label"
            :api="field.categoryApi!"
            @update:model-value="setFieldValue(field.key, $event)"
          />

          <CheckboxGroupSelect
            v-else-if="field.type === 'checkbox-group'"
            :model-value="values[field.key]"
            :label="field.label"
            :api="field.categoryApi!"
            @update:model-value="setFieldValue(field.key, $event)"
          />

          <UFieldGroup v-else-if="field.type === 'number' && field.unit" class="w-full">
            <UInputNumber
              :model-value="values[field.key]"
              :color="errors[field.key] ? 'error' : undefined"
              :step="field.step"
              :disabled="!!field.computed"
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
            :step="field.step"
            orientation="vertical"
            class="w-full"
            @update:model-value="setFieldValue(field.key, $event)"
          />

          <DurationValueInput
            v-else-if="field.type === 'duration'"
            :model-value="values[field.key]"
            :invalid="!!errors[field.key]"
            :units="field.durationUnits"
            @update:model-value="setFieldValue(field.key, $event)"
          />

          <UTextarea
            v-else-if="field.type === 'textarea'"
            :model-value="values[field.key]"
            :rows="2"
            class="w-full"
            @update:model-value="setFieldValue(field.key, $event)"
          />

          <div v-else-if="field.type === 'repeatable-group'" class="flex flex-col gap-2">
            <label class="font-medium text-sm">{{ field.label }}</label>

            <UCard
              v-for="(row, index) in values[field.key] ?? []"
              :key="row._rowId"
              :ui="{ body: 'flex flex-col sm:flex-row gap-2 sm:items-end p-3 sm:p-3' }"
            >
              <div v-for="rowField in field.rowFields" :key="rowField.key" class="flex-1">
                <CategorySelect
                  v-if="rowField.type === 'category'"
                  :model-value="row[rowField.key]"
                  :label="rowField.label"
                  :api="rowField.categoryApi!"
                  @update:model-value="setRowValue(field, index, rowField.key, $event)"
                />

                <template v-else>
                  <label class="font-medium text-sm">{{ rowField.label }}</label>

                  <UFieldGroup v-if="rowField.type === 'number' && rowField.unit" class="w-full">
                    <UInputNumber
                      :model-value="row[rowField.key]"
                      orientation="vertical"
                      class="w-full"
                      @update:model-value="setRowValue(field, index, rowField.key, $event)"
                    />
                    <UBadge color="neutral" variant="outline" size="lg" :label="rowField.unit" />
                  </UFieldGroup>

                  <UInputNumber
                    v-else-if="rowField.type === 'number'"
                    :model-value="row[rowField.key]"
                    orientation="vertical"
                    class="w-full"
                    @update:model-value="setRowValue(field, index, rowField.key, $event)"
                  />

                  <UInput
                    v-else
                    :model-value="row[rowField.key]"
                    class="w-full"
                    @update:model-value="setRowValue(field, index, rowField.key, $event)"
                  />
                </template>
              </div>

              <UButton
                icon="i-lucide-trash-2"
                color="error"
                variant="ghost"
                :aria-label="`Remove ${field.label.toLowerCase()} row`"
                @click="removeRow(field, index)"
              />
            </UCard>

            <UButton
              :label="field.addRowLabel ?? 'Add row'"
              icon="i-lucide-plus"
              variant="ghost"
              size="sm"
              class="self-start"
              @click="addRow(field)"
            />
          </div>

          <UInput
            v-else-if="field.type !== 'boolean'"
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
        :label="editingId === null ? `Add ${config?.entryLabel ?? 'entry'}` : 'Save changes'"
        icon="i-lucide-save"
        :loading="submitting"
        @click="submitForm"
      />
    </template>
  </UModal>
</template>
