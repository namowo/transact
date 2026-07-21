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
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import CategorySelect from '@/components/scenarios/CategorySelect.vue'
import { getLabMethodConfig, type MethodFieldConfig } from '@/data/labMethods'
import { samplingMethodApi } from '@/api/methods'
import { useAuthStore } from '@/stores/auth'

// Every sub-method field is optional at the API (a tab left blank is simply
// skipped on submit), so the schema only enforces each field's type.
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

const props = defineProps<{ id?: string }>()

const router = useRouter()
const auth = useAuthStore()
const laboratoryId = computed(() => auth.user?.laboratory_id ?? null)

const editingId = computed(() => (props.id ? Number(props.id) : null))

const subMethodKeys = ['swab', 'tape', 'vacuum', 'cutting', 'scraping', 'picking'] as const
type SubMethodKey = (typeof subMethodKeys)[number]

const subMethodConfigs = subMethodKeys.map((key) => getLabMethodConfig(key)!)

function emptyForm(fields: MethodFieldConfig[]): Record<string, any> {
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
    useForm<Record<string, any>>({
      validationSchema: schemaForFields(config.fields),
      initialValues: emptyForm(config.fields),
    }),
  ]),
) as Record<SubMethodKey, ReturnType<typeof useForm<Record<string, any>>>>

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
const existingSubMethodIds = ref<Record<SubMethodKey, number | null>>(
  Object.fromEntries(subMethodKeys.map((key) => [key, null])) as Record<
    SubMethodKey,
    number | null
  >,
)

const loading = ref(false)
const loadError = ref('')
const submitting = ref(false)
const submitError = ref('')

onMounted(async () => {
  if (editingId.value === null) return
  loading.value = true
  loadError.value = ''
  try {
    const sampling = await samplingMethodApi.list().then((all) => all.find((s) => s.id === editingId.value))
    if (!sampling) {
      loadError.value = 'This sampling method could not be found.'
      return
    }
    for (const config of subMethodConfigs) {
      const key = config.key as SubMethodKey
      const subMethod = (sampling as any)[`${key}_method`]
      existingSubMethodIds.value[key] = subMethod?.id ?? null
      if (subMethod) {
        const next = emptyForm(config.fields)
        for (const field of config.fields) {
          next[field.key] = subMethod[field.key] ?? (field.type === 'boolean' ? false : null)
        }
        subForms[key].resetForm({ values: next })
      }
    }
  } catch {
    loadError.value = 'Could not load this sampling method.'
  } finally {
    loading.value = false
  }
})

// A sub-method tab is only saved if the user filled in at least one field.
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

    const subMethodIds: Record<SubMethodKey, number | null> = {} as any

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

    router.push({ name: 'settings-methods-sampling' })
  } catch {
    submitError.value = 'Could not save this sampling method. Please try again.'
  } finally {
    submitting.value = false
  }
}

function onCancel() {
  router.push({ name: 'settings-methods-sampling' })
}
</script>

<template>
  <div class="flex flex-col gap-6 max-w-3xl">
    <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">
      {{ editingId === null ? 'Add sampling method' : 'Edit sampling method' }}
    </h1>

    <div v-if="loading" class="flex justify-center py-12">
      <ProgressSpinner style="width: 3rem; height: 3rem" />
    </div>

    <Message v-else-if="loadError" severity="error" size="small">{{ loadError }}</Message>

    <form v-else class="flex flex-col gap-4" @submit.prevent="onSubmit">
      <p class="text-sm text-surface-500 dark:text-surface-400">
        Fill in the sub-methods that are relevant for this sampling method. Tabs left empty are
        skipped.
      </p>

      <Tabs value="swab">
        <TabList>
          <Tab v-for="config in subMethodConfigs" :key="config.key" :value="config.key">
            {{ config.label }}
          </Tab>
        </TabList>
        <TabPanels>
          <TabPanel v-for="config in subMethodConfigs" :key="config.key" :value="config.key">
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

                <InputNumber
                  v-else-if="field.type === 'number'"
                  :model-value="fieldValue(config.key as typeof subMethodKeys[number], field.key)"
                  :invalid="!!fieldError(config.key as typeof subMethodKeys[number], field.key)"
                  fluid
                  @update:model-value="
                    setFieldValue(config.key as typeof subMethodKeys[number], field.key, $event)
                  "
                />

                <div v-else-if="field.type === 'boolean'" class="flex items-center gap-2">
                  <ToggleSwitch
                    :model-value="fieldValue(config.key as typeof subMethodKeys[number], field.key)"
                    :input-id="`${config.key}-${field.key}`"
                    @update:model-value="
                      setFieldValue(config.key as typeof subMethodKeys[number], field.key, $event)
                    "
                  />
                </div>

                <Textarea
                  v-else-if="field.type === 'textarea'"
                  :model-value="fieldValue(config.key as typeof subMethodKeys[number], field.key)"
                  rows="2"
                  fluid
                  @update:model-value="
                    setFieldValue(config.key as typeof subMethodKeys[number], field.key, $event)
                  "
                />

                <InputText
                  v-else
                  :model-value="fieldValue(config.key as typeof subMethodKeys[number], field.key)"
                  fluid
                  @update:model-value="
                    setFieldValue(config.key as typeof subMethodKeys[number], field.key, $event)
                  "
                />

                <Message
                  v-if="fieldError(config.key as typeof subMethodKeys[number], field.key)"
                  severity="error"
                  size="small"
                  variant="simple"
                >
                  {{ fieldError(config.key as typeof subMethodKeys[number], field.key) }}
                </Message>
              </div>
            </div>
          </TabPanel>
        </TabPanels>
      </Tabs>

      <Message v-if="submitError" severity="error" size="small">{{ submitError }}</Message>

      <div class="flex gap-2 mt-2">
        <Button
          type="submit"
          :label="editingId === null ? 'Add sampling method' : 'Save changes'"
          :loading="submitting"
        />
        <Button label="Cancel" text type="button" @click="onCancel" />
      </div>
    </form>
  </div>
</template>
