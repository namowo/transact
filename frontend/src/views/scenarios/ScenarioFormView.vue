<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useFieldArray, useForm } from 'vee-validate'
import * as yup from 'yup'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import Button from 'primevue/button'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import CategorySelect from '@/components/scenarios/CategorySelect.vue'
import ContactTemplateCard from '@/components/scenarios/ContactTemplateCard.vue'
import DurationInput from '@/components/scenarios/DurationInput.vue'
import {
  scenarioCategoryApi,
  disturbanceCategoryApi,
  geographicLocationCategoryApi,
} from '@/api/categories'
import { getScenario, createScenario, updateScenario } from '@/api/scenarios'
import {
  emptyPersistenceDraft,
  persistenceDraftFromPersistence,
  savePersistenceDraft,
} from '@/components/scenarios/persistenceDraft'
import {
  contactTemplateDraftFromContactTemplate,
  emptyContactTemplateDraft,
  saveContactTemplateDraft,
} from '@/components/scenarios/contactTemplateDraft'
import type { ContactTemplateDraft } from '@/components/scenarios/contactTemplateDraft'

const props = defineProps<{ studyId: string; id?: string }>()

const router = useRouter()

const studyId = computed(() => Number(props.studyId))
const editingId = computed(() => (props.id ? Number(props.id) : null))

const loading = ref(false)
const loadError = ref('')
const submitting = ref(false)
const submitError = ref('')

interface ScenarioFormValues {
  realistic: boolean
  scenarioCategoryId: number | null
  persistence: ReturnType<typeof emptyPersistenceDraft>
  contactTemplates: ContactTemplateDraft[]
}

const schema = yup.object({
  realistic: yup.boolean().defined(),
  scenarioCategoryId: yup.number().nullable().required('Please select a scenario category.'),
  persistence: yup.object({
    intervalOfPersistence: yup
      .number()
      .nullable()
      .min(0, 'Interval of persistence must be zero or greater.'),
    temperature: yup.number().nullable().defined(),
    humidity: yup
      .number()
      .nullable()
      .min(0, 'Humidity must be between 0 and 100.')
      .max(100, 'Humidity must be between 0 and 100.'),
    uvIrradiation: yup.number().nullable().min(0, 'UV irradiation must be zero or greater.'),
    indoors: yup.boolean().defined(),
    changeOverTime: yup.boolean().defined(),
    durationOfDisturbance: yup
      .number()
      .nullable()
      .min(0, 'Duration of disturbance must be zero or greater.'),
    descriptionOfDisturbance: yup.string().nullable().defined(),
    disturbanceCategoryId: yup.number().nullable().defined(),
    geographicLocationCategoryId: yup.number().nullable().defined(),
  }),
  contactTemplates: yup.array().of(
    yup.object({
      duration: yup.number().nullable().min(0, 'Duration must be zero or greater.'),
      pressure: yup.number().nullable().min(0, 'Pressure must be zero or greater.'),
      frictionApplied: yup.number().nullable().min(0, 'Friction applied must be zero or greater.'),
      contactArea: yup.number().nullable().min(0, 'Contact area must be zero or greater.'),
      temperature: yup.number().nullable().defined(),
      humidity: yup
        .number()
        .nullable()
        .min(0, 'Humidity must be between 0 and 100.')
        .max(100, 'Humidity must be between 0 and 100.'),
      uvIrradiation: yup.number().nullable().min(0, 'UV irradiation must be zero or greater.'),
    }),
  ),
})

const { defineField, errors, handleSubmit, setValues } = useForm<ScenarioFormValues>({
  validationSchema: schema,
  initialValues: {
    realistic: true,
    scenarioCategoryId: null,
    persistence: emptyPersistenceDraft(),
    contactTemplates: [emptyContactTemplateDraft()],
  },
})

const [realistic] = defineField('realistic')
const [scenarioCategoryId] = defineField('scenarioCategoryId')
const [intervalOfPersistence] = defineField('persistence.intervalOfPersistence')
const [temperature] = defineField('persistence.temperature')
const [humidity] = defineField('persistence.humidity')
const [uvIrradiation] = defineField('persistence.uvIrradiation')
const [indoors] = defineField('persistence.indoors')
const [changeOverTime] = defineField('persistence.changeOverTime')
const [durationOfDisturbance] = defineField('persistence.durationOfDisturbance')
const [descriptionOfDisturbance] = defineField('persistence.descriptionOfDisturbance')
const [disturbanceCategoryId] = defineField('persistence.disturbanceCategoryId')
const [geographicLocationCategoryId] = defineField('persistence.geographicLocationCategoryId')

const {
  fields: contactTemplateFields,
  push: pushContactTemplate,
  remove: removeContactTemplateField,
} = useFieldArray<ContactTemplateDraft>('contactTemplates')

const collapsedContactTemplates = ref<boolean[]>([false])

// The scenario's own persistence link(s); loaded so an edit doesn't drop
// other persistencies already linked to this scenario.
let existingPersistenceIds: number[] = []

onMounted(async () => {
  if (editingId.value === null) return

  loading.value = true
  try {
    const scenario = await getScenario(editingId.value)
    const contactTemplates = scenario.contact_templates.length
      ? scenario.contact_templates.map(contactTemplateDraftFromContactTemplate)
      : [emptyContactTemplateDraft()]
    existingPersistenceIds = scenario.persistencies.map((p) => p.id)
    setValues({
      realistic: !!scenario.realistic,
      scenarioCategoryId: scenario.scenario_category_id ?? null,
      persistence: persistenceDraftFromPersistence(scenario.persistencies[0] ?? null),
      contactTemplates,
    })
    // Existing contact templates start collapsed so the form doesn't open on
    // a wall of fields; a single freshly-added template starts expanded.
    collapsedContactTemplates.value = contactTemplates.map(
      () => scenario.contact_templates.length > 0,
    )
  } catch {
    loadError.value = 'Could not load this scenario.'
  } finally {
    loading.value = false
  }
})

function addContactTemplate() {
  collapsedContactTemplates.value = collapsedContactTemplates.value.map(() => true)
  pushContactTemplate(emptyContactTemplateDraft())
  collapsedContactTemplates.value.push(false)
}

function removeContactTemplate(index: number) {
  removeContactTemplateField(index)
  collapsedContactTemplates.value.splice(index, 1)
}

const onSubmit = handleSubmit(async (values) => {
  submitting.value = true
  submitError.value = ''
  try {
    const persistenceId = await savePersistenceDraft(values.persistence)
    const persistenceIds = persistenceId
      ? Array.from(new Set([...existingPersistenceIds, persistenceId]))
      : existingPersistenceIds

    const payload = {
      realistic: values.realistic,
      scenario_category_id: values.scenarioCategoryId,
      study_ids: [studyId.value],
      persistence_ids: persistenceIds,
    }

    const scenario = editingId.value
      ? await updateScenario(editingId.value, payload)
      : await createScenario(payload)

    const contactTemplateIds: number[] = []
    for (const contactTemplate of values.contactTemplates) {
      contactTemplateIds.push(await saveContactTemplateDraft(contactTemplate, scenario.id))
    }
    await updateScenario(scenario.id, { contact_template_ids: contactTemplateIds })

    router.push({ name: 'scenarios', params: { studyId: studyId.value } })
  } catch {
    submitError.value = 'Could not save the scenario. Please try again.'
  } finally {
    submitting.value = false
  }
})

function onCancel() {
  router.push({ name: 'scenarios', params: { studyId: studyId.value } })
}
</script>

<template>
  <div class="flex flex-col gap-6 max-w-3xl">
    <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">
      {{ editingId === null ? 'Add scenario' : 'Edit scenario' }}
    </h1>

    <div v-if="loading" class="flex justify-center py-12">
      <ProgressSpinner style="width: 3rem; height: 3rem" />
    </div>

    <Message v-else-if="loadError" severity="error" size="small">{{ loadError }}</Message>

    <form v-else class="flex flex-col gap-4" @submit.prevent="onSubmit">
      <Tabs value="details">
        <TabList>
          <Tab value="details">Details</Tab>
          <Tab value="persistence">Persistence</Tab>
          <Tab value="contactTemplates">
            Contact templates ({{ contactTemplateFields.length }})
          </Tab>
        </TabList>
        <TabPanels>
          <TabPanel value="details">
            <div class="flex flex-col gap-4">
              <div class="flex flex-col gap-2">
                <CategorySelect
                  v-model="scenarioCategoryId"
                  label="Scenario category"
                  :api="scenarioCategoryApi"
                />
                <Message
                  v-if="errors.scenarioCategoryId"
                  severity="error"
                  size="small"
                  variant="simple"
                >
                  {{ errors.scenarioCategoryId }}
                </Message>
              </div>

              <div class="flex items-center gap-2">
                <ToggleSwitch v-model="realistic" input-id="realistic" />
                <label for="realistic" class="text-sm">Realistic scenario</label>
              </div>
            </div>
          </TabPanel>

          <TabPanel value="persistence">
            <div class="flex flex-col gap-4">
              <div class="flex flex-col gap-2">
                <label class="font-medium text-sm">Interval of persistence (Optional)</label>
                <DurationInput v-model="intervalOfPersistence" />
                <Message
                  v-if="errors['persistence.intervalOfPersistence']"
                  severity="error"
                  size="small"
                  variant="simple"
                >
                  {{ errors['persistence.intervalOfPersistence'] }}
                </Message>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="flex flex-col gap-2">
                  <label class="font-medium text-sm">Temperature (°C)</label>
                  <InputNumber v-model="temperature" fluid />
                </div>
                <div class="flex flex-col gap-2">
                  <label class="font-medium text-sm">Humidity (%)</label>
                  <InputNumber
                    v-model="humidity"
                    :invalid="!!errors['persistence.humidity']"
                    fluid
                  />
                  <Message
                    v-if="errors['persistence.humidity']"
                    severity="error"
                    size="small"
                    variant="simple"
                  >
                    {{ errors['persistence.humidity'] }}
                  </Message>
                </div>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="flex flex-col gap-2">
                  <label class="font-medium text-sm">UV irradiation (Optional)</label>
                  <InputNumber
                    v-model="uvIrradiation"
                    :invalid="!!errors['persistence.uvIrradiation']"
                    fluid
                  />
                  <Message
                    v-if="errors['persistence.uvIrradiation']"
                    severity="error"
                    size="small"
                    variant="simple"
                  >
                    {{ errors['persistence.uvIrradiation'] }}
                  </Message>
                </div>
                <div class="flex flex-col gap-2">
                  <label class="font-medium text-sm"
                    >Duration of disturbance (seconds, Optional)</label
                  >
                  <InputNumber
                    v-model="durationOfDisturbance"
                    :invalid="!!errors['persistence.durationOfDisturbance']"
                    fluid
                  />
                  <Message
                    v-if="errors['persistence.durationOfDisturbance']"
                    severity="error"
                    size="small"
                    variant="simple"
                  >
                    {{ errors['persistence.durationOfDisturbance'] }}
                  </Message>
                </div>
              </div>
              <div class="flex flex-wrap gap-6">
                <div class="flex items-center gap-2">
                  <ToggleSwitch v-model="indoors" input-id="indoors" />
                  <label for="indoors" class="text-sm">Indoors</label>
                </div>
                <div class="flex items-center gap-2">
                  <ToggleSwitch v-model="changeOverTime" input-id="change-over-time" />
                  <label for="change-over-time" class="text-sm">Changes over time</label>
                </div>
              </div>
              <CategorySelect
                v-model="disturbanceCategoryId"
                label="Disturbance"
                :api="disturbanceCategoryApi"
              />
              <CategorySelect
                v-model="geographicLocationCategoryId"
                label="Geographic location"
                :api="geographicLocationCategoryApi"
              />
              <div class="flex flex-col gap-2">
                <label class="font-medium text-sm">Description of disturbance (Optional)</label>
                <Textarea v-model="descriptionOfDisturbance" rows="2" fluid />
              </div>
            </div>
          </TabPanel>

          <TabPanel value="contactTemplates">
            <div class="flex flex-col gap-4">
              <ContactTemplateCard
                v-for="(contactTemplateField, index) in contactTemplateFields"
                :key="contactTemplateField.key"
                v-model="contactTemplateField.value"
                :errors="errors"
                :index="index"
                :collapsed="collapsedContactTemplates[index]"
                :removable="contactTemplateFields.length > 1"
                @update:collapsed="collapsedContactTemplates[index] = $event"
                @remove="removeContactTemplate(index)"
              />

              <Button
                label="Add contact template"
                icon="pi pi-plus"
                outlined
                class="self-start"
                @click="addContactTemplate"
              />
            </div>
          </TabPanel>
        </TabPanels>
      </Tabs>

      <Message v-if="submitError" severity="error" size="small">{{ submitError }}</Message>

      <div class="flex gap-2 mt-2">
        <Button
          type="submit"
          :label="editingId === null ? 'Add scenario' : 'Save changes'"
          :loading="submitting"
        />
        <Button label="Cancel" text type="button" @click="onCancel" />
      </div>
    </form>
  </div>
</template>
