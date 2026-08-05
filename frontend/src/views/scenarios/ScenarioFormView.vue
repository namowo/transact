<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useFieldArray, useForm } from 'vee-validate'
import * as yup from 'yup'
import ToggleSwitch from 'primevue/toggleswitch'
import Button from 'primevue/button'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Divider from 'primevue/divider'
import Select from 'primevue/select'
import ConfirmDialog from 'primevue/confirmdialog'
import { useToast } from 'primevue/usetoast'
import Stepper from 'primevue/stepper'
import StepList from 'primevue/steplist'
import StepPanels from 'primevue/steppanels'
import Step from 'primevue/step'
import StepPanel from 'primevue/steppanel'
import CategorySelect from '@/components/scenarios/CategorySelect.vue'
import ContactTemplateCard from '@/components/scenarios/ContactTemplateCard.vue'
import PersistenceCard from '@/components/scenarios/PersistenceCard.vue'
import { scenarioCategoryApi } from '@/api/categories'
import { getScenario, createScenario, updateScenario } from '@/api/scenarios'
import { listPersistences } from '@/api/persistences'
import {
  emptyPersistenceDraft,
  isBlankPersistenceDraft,
  isPersistenceEditable,
  persistenceDraftFromPersistence,
  persistenceLabel,
  savePersistenceDraft,
} from '@/components/scenarios/persistenceDraft'
import type { PersistenceDraft } from '@/components/scenarios/persistenceDraft'
import type { Persistence } from '@/api/types'
import {
  contactTemplateDraftFromContactTemplate,
  emptyContactTemplateDraft,
  isBlankContactTemplateDraft,
  saveContactTemplateDraft,
} from '@/components/scenarios/contactTemplateDraft'
import type { ContactTemplateDraft } from '@/components/scenarios/contactTemplateDraft'

const props = defineProps<{ studyId: string; id?: string }>()

const route = useRoute()
const router = useRouter()
const toast = useToast()

const studyId = computed(() => Number(props.studyId))
const editingId = computed(() => (props.id ? Number(props.id) : null))

const loading = ref(false)
const loadError = ref('')
const submitting = ref(false)
const submitError = ref('')

// Only the study that originally created a scenario may edit it; other
// studies can only link/unlink it via ScenariosList, since it's a shared
// record they don't own.
const owningStudyId = ref<number | null>(null)
const isEditable = computed(
  () => owningStudyId.value === null || owningStudyId.value === studyId.value,
)

// Which step to open, kept in the URL like the study workflow's stepper so
// deep links and reloads land on the same step.
const validSteps = ['details', 'persistence', 'contact-templates'] as const
type StepName = (typeof validSteps)[number]
const stepToPanel: Record<StepName, string> = {
  details: '1',
  persistence: '2',
  'contact-templates': '3',
}
const panelToStep: Record<string, StepName> = {
  '1': 'details',
  '2': 'persistence',
  '3': 'contact-templates',
}

function stepFromQuery(): StepName {
  const step = route.query.step
  return (validSteps as readonly string[]).includes(step as string) ? (step as StepName) : 'details'
}

const activeStep = computed<string>({
  get: () => stepToPanel[stepFromQuery()],
  set: (value) => {
    router.replace({ query: { ...route.query, step: panelToStep[value] ?? 'details' } })
  },
})

interface ScenarioFormValues {
  realistic: boolean
  scenarioCategoryId: number | null
  persistencies: PersistenceDraft[]
  contactTemplates: ContactTemplateDraft[]
}

const persistenceSchema = yup.object({
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
})

const schema = yup.object({
  realistic: yup.boolean().defined(),
  scenarioCategoryId: yup.number().nullable().required('Please select a scenario category.'),
  persistencies: yup.array().of(persistenceSchema),
  contactTemplates: yup.array().of(
    yup.object({
      duration: yup.number().nullable().min(0, 'Duration must be zero or greater.'),
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

const { defineField, errors, handleSubmit, setValues, values } = useForm<ScenarioFormValues>({
  validationSchema: schema,
  initialValues: {
    realistic: true,
    scenarioCategoryId: null,
    persistencies: [],
    contactTemplates: [emptyContactTemplateDraft()],
  },
})

const [realistic] = defineField('realistic')
const [scenarioCategoryId] = defineField('scenarioCategoryId')

const {
  fields: persistenceFields,
  push: pushPersistence,
  remove: removePersistenceField,
} = useFieldArray<PersistenceDraft>('persistencies')

const {
  fields: contactTemplateFields,
  push: pushContactTemplate,
  remove: removeContactTemplateField,
} = useFieldArray<ContactTemplateDraft>('contactTemplates')

const collapsedPersistencies = ref<boolean[]>([])
const collapsedContactTemplates = ref<boolean[]>([false])

const existingPersistences = ref<Persistence[]>([])
const existingPersistencesLoading = ref(false)
const selectedExistingPersistenceId = ref<number | null>(null)

const availableExistingPersistences = computed(() => {
  const usedIds = new Set(values.persistencies.map((p) => p.id).filter((id): id is number => !!id))
  return existingPersistences.value.filter((p) => !usedIds.has(p.id))
})

onMounted(async () => {
  existingPersistencesLoading.value = true
  listPersistences()
    .then((data) => (existingPersistences.value = data))
    .finally(() => (existingPersistencesLoading.value = false))

  if (editingId.value === null) return

  loading.value = true
  try {
    const scenario = await getScenario(editingId.value)
    owningStudyId.value = scenario.owning_study_id ?? null
    const persistencies = scenario.persistencies.map((p) => persistenceDraftFromPersistence(p))
    const contactTemplates = scenario.contact_templates.length
      ? scenario.contact_templates.map(contactTemplateDraftFromContactTemplate)
      : [emptyContactTemplateDraft()]
    setValues({
      realistic: !!scenario.realistic,
      scenarioCategoryId: scenario.scenario_category_id ?? null,
      persistencies,
      contactTemplates,
    })
    // Existing entries start collapsed so the form doesn't open on a wall of
    // fields; freshly-added ones start expanded.
    collapsedPersistencies.value = persistencies.map(() => true)
    collapsedContactTemplates.value = contactTemplates.map(
      () => scenario.contact_templates.length > 0,
    )
  } catch {
    loadError.value = 'Could not load this scenario.'
  } finally {
    loading.value = false
  }
})

function addPersistence() {
  collapsedPersistencies.value = collapsedPersistencies.value.map(() => true)
  pushPersistence(emptyPersistenceDraft())
  collapsedPersistencies.value.push(false)
}

function addExistingPersistence() {
  const persistence = existingPersistences.value.find(
    (p) => p.id === selectedExistingPersistenceId.value,
  )
  if (!persistence) return

  collapsedPersistencies.value = collapsedPersistencies.value.map(() => true)
  pushPersistence(persistenceDraftFromPersistence(persistence))
  collapsedPersistencies.value.push(true)
  selectedExistingPersistenceId.value = null
}

function removePersistence(index: number) {
  removePersistenceField(index)
  collapsedPersistencies.value.splice(index, 1)
}

function addContactTemplate() {
  collapsedContactTemplates.value = collapsedContactTemplates.value.map(() => true)
  pushContactTemplate(emptyContactTemplateDraft())
  collapsedContactTemplates.value.push(false)
}

function removeContactTemplate(index: number) {
  removeContactTemplateField(index)
  collapsedContactTemplates.value.splice(index, 1)
}

// The workflow mirrors the study stepper: details, persistence, contact
// templates. Saving is only allowed once each step has real content -
// otherwise the user is nudged back to whichever step is still empty.
function firstIncompleteStep(): { step: StepName; message: string } | null {
  if (!values.scenarioCategoryId) {
    return { step: 'details', message: 'Please choose a scenario category before saving.' }
  }
  if (!values.persistencies.some((p) => !isBlankPersistenceDraft(p))) {
    return {
      step: 'persistence',
      message: 'Add at least one persistence before saving this scenario.',
    }
  }
  if (!values.contactTemplates.some((c) => !isBlankContactTemplateDraft(c))) {
    return {
      step: 'contact-templates',
      message: 'Add at least one contact template before saving this scenario.',
    }
  }
  return null
}

const onSubmit = handleSubmit(async (formValues) => {
  if (!isEditable.value) return

  const incomplete = firstIncompleteStep()
  if (incomplete) {
    activeStep.value = stepToPanel[incomplete.step]
    toast.add({ severity: 'warn', summary: 'Scenario incomplete', detail: incomplete.message, life: 5000 })
    return
  }

  submitting.value = true
  submitError.value = ''
  try {
    const persistenceIds: number[] = []
    for (const persistence of formValues.persistencies) {
      const persistenceId = await savePersistenceDraft(persistence, studyId.value)
      if (persistenceId) persistenceIds.push(persistenceId)
    }

    const payload = {
      realistic: formValues.realistic,
      scenario_category_id: formValues.scenarioCategoryId,
      study_ids: [studyId.value],
      persistence_ids: Array.from(new Set(persistenceIds)),
      ...(editingId.value === null ? { owning_study_id: studyId.value } : {}),
    }

    const scenario = editingId.value
      ? await updateScenario(editingId.value, payload)
      : await createScenario(payload)

    const contactTemplateIds: number[] = []
    for (const contactTemplate of formValues.contactTemplates) {
      contactTemplateIds.push(await saveContactTemplateDraft(contactTemplate, scenario.id))
    }
    await updateScenario(scenario.id, { contact_template_ids: contactTemplateIds })

    router.push({
      name: 'studies-edit',
      params: { id: studyId.value },
      query: { step: 'planning' },
    })
  } catch {
    submitError.value = 'Could not save the scenario. Please try again.'
  } finally {
    submitting.value = false
  }
})

function onCancel() {
  router.push({
    name: 'studies-edit',
    params: { id: studyId.value },
    query: { step: 'planning' },
  })
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <ConfirmDialog />

    <div class="flex flex-col gap-1">
      <Button
        label="Back to study"
        icon="pi pi-arrow-left"
        text
        size="small"
        class="self-start -ml-3!"
        @click="onCancel"
      />
      <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">
        {{ editingId === null ? 'Add scenario' : 'Edit scenario' }}
      </h1>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <ProgressSpinner style="width: 3rem; height: 3rem" />
    </div>

    <Message v-else-if="loadError" severity="error" size="small">{{ loadError }}</Message>

    <Message v-else-if="!isEditable" severity="info" size="small">
      This scenario was created for another study, so it can only be edited there. You can still
      view it here, or remove it from this study on the scenarios list.
    </Message>

    <form v-else class="flex flex-col gap-4" @submit.prevent="onSubmit">
      <Stepper v-model:value="activeStep" :linear="false">
        <StepList class="sticky top-0 z-10 bg-surface-0 dark:bg-surface-900">
          <Step value="1">Details</Step>
          <Step value="2">Persistence</Step>
          <Step value="3">Contact templates ({{ contactTemplateFields.length }})</Step>
        </StepList>
        <StepPanels>
          <StepPanel value="1" class="bg-transparent!">
            <div class="flex flex-col gap-4 max-w-2xl">
              <div class="flex flex-col gap-2">
                <CategorySelect
                  v-model="scenarioCategoryId"
                  label="Scenario category"
                  description="Use the label that you are also using in the sheet 'Activity Scenarios'. Provide the corresponding reference profiles in the sheet 'Reference Profiles'."
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

              <div class="flex justify-end mt-2">
                <Button label="Continue" icon="pi pi-arrow-right" icon-pos="right" @click="activeStep = '2'" />
              </div>
            </div>
          </StepPanel>

          <StepPanel value="2" class="bg-transparent!">
            <div class="flex flex-col gap-4">
              <p
                v-if="persistenceFields.length === 0"
                class="text-sm text-surface-500 dark:text-surface-400"
              >
                No persistence linked yet.
              </p>

              <PersistenceCard
                v-for="(persistenceField, index) in persistenceFields"
                :key="persistenceField.key"
                v-model="persistenceField.value"
                :errors="errors"
                :index="index"
                :collapsed="collapsedPersistencies[index]"
                :removable="true"
                :editable="isPersistenceEditable(persistenceField.value, studyId)"
                @update:collapsed="collapsedPersistencies[index] = $event"
                @remove="removePersistence(index)"
              />

              <div class="flex flex-col gap-4">
                <Button
                  label="Add new persistence"
                  icon="pi pi-plus"
                  outlined
                  class="self-start"
                  @click="addPersistence"
                />

                <div class="flex flex-col gap-2">
                  <label class="font-medium text-sm">Link an existing persistence</label>
                  <div class="flex gap-2">
                    <Select
                      v-model="selectedExistingPersistenceId"
                      :options="availableExistingPersistences"
                      :option-label="persistenceLabel"
                      option-value="id"
                      :loading="existingPersistencesLoading"
                      placeholder="Select an existing persistence"
                      filter
                      show-clear
                      fluid
                    >
                      <template #option="{ option }">{{ persistenceLabel(option) }}</template>
                      <template #value="{ value }">
                        <span v-if="value">
                          {{ persistenceLabel(existingPersistences.find((p) => p.id === value)!) }}
                        </span>
                      </template>
                    </Select>
                    <Button
                      label="Link"
                      :disabled="!selectedExistingPersistenceId"
                      @click="addExistingPersistence"
                    />
                  </div>
                </div>
              </div>

              <div class="flex justify-between mt-2">
                <Button label="Back" icon="pi pi-arrow-left" text @click="activeStep = '1'" />
                <Button
                  label="Continue"
                  icon="pi pi-arrow-right"
                  icon-pos="right"
                  @click="activeStep = '3'"
                />
              </div>
            </div>
          </StepPanel>

          <StepPanel value="3" class="bg-transparent!">
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

              <div class="flex justify-start mt-2">
                <Button label="Back" icon="pi pi-arrow-left" text @click="activeStep = '2'" />
              </div>
            </div>
          </StepPanel>
        </StepPanels>
      </Stepper>

      <Divider />

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
