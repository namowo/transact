<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { watchDebounced } from '@vueuse/core'
import { useFieldArray, useForm } from 'vee-validate'
import * as yup from 'yup'
import { useToast } from '@nuxt/ui/composables'
import type { StepperItem } from '@nuxt/ui'
import CategorySelect from './CategorySelect.vue'
import ContactTemplateCard from './ContactTemplateCard.vue'
import PersistenceCard from './PersistenceCard.vue'
import PersistencePickerDialog from './PersistencePickerDialog.vue'
import { scenarioCategoryApi } from '@/api/categories'
import { getScenario, listScenarios, createScenario, updateScenario } from '@/api/scenarios'
import {
  clonePersistenceDraftForDuplication,
  emptyPersistenceDraft,
  isBlankPersistenceDraft,
  isPersistenceEditable,
  persistenceDraftFromPersistence,
  savePersistenceDraft,
} from './persistenceDraft'
import type { PersistenceDraft } from './persistenceDraft'
import type { Persistence, Scenario } from '@/api/types'
import {
  cloneContactTemplateDraftForDuplication,
  contactTemplateDraftFromContactTemplate,
  emptyContactTemplateDraft,
  isBlankContactTemplateDraft,
  saveContactTemplateDraft,
} from './contactTemplateDraft'
import type { ContactTemplateDraft } from './contactTemplateDraft'

const props = defineProps<{
  studyId: string
  // Id of the scenario being edited, or null/undefined when adding a new one.
  id?: string | null
  // Id of a source scenario to pre-fill the new scenario's drafts from (only
  // used when id is not set).
  duplicateFromId?: string | null
}>()

const emit = defineEmits<{
  saved: []
}>()

const open = defineModel<boolean>('open', { default: false })

const toast = useToast()

const studyId = computed(() => props.studyId)
const editingId = computed(() => props.id ?? null)
const duplicateFromId = computed(() => (editingId.value === null ? props.duplicateFromId ?? null : null))

const loading = ref(false)
const loadError = ref('')
const submitting = ref(false)
const submitError = ref('')

// Only the study that originally created a scenario may edit it; other
// studies can only link/unlink it via ScenariosList, since it's a shared
// record they don't own.
const owningStudyId = ref<string | null>(null)
const isEditable = computed(
  () => owningStudyId.value === null || owningStudyId.value === studyId.value,
)

// Which step is open within the dialog. Kept as local state instead of the
// URL since the form no longer has its own route.
const validSteps = ['details', 'persistence', 'contact-templates'] as const
type StepName = (typeof validSteps)[number]
const stepToPanel: Record<StepName, string> = {
  details: '1',
  persistence: '2',
  'contact-templates': '3',
}

const activeStep = ref('1')

const stepItems = computed<StepperItem[]>(() => [
  { value: '1', title: 'Details', slot: '1' },
  { value: '2', title: 'Persistence', slot: '2' },
  {
    value: '3',
    title: `Contact templates (${contactTemplateFields.value.length})`,
    slot: '3',
  },
])

interface ScenarioFormValues {
  realistic: boolean
  scenarioCategoryId: string | null
  persistencies: PersistenceDraft[]
  contactTemplates: ContactTemplateDraft[]
}

// UInputNumber emits NaN (not null) when cleared, so every optional numeric
// field needs this transform before its other checks run - otherwise
// clearing the field makes yup's nullable() type check fail with a
// confusing "must be a number" error on a field the user left empty.
const nanToNull = (value: unknown) => (typeof value === 'number' && Number.isNaN(value) ? null : value)

const persistenceSchema = yup.object({
  intervalOfPersistence: yup
    .number()
    .transform(nanToNull)
    .nullable()
    .min(0, 'Interval of persistence must be zero or greater.'),
  temperature: yup.number().transform(nanToNull).nullable().defined(),
  humidity: yup
    .number()
    .transform(nanToNull)
    .nullable()
    .min(0, 'Humidity must be between 0 and 100%.')
    .max(1, 'Humidity must be between 0 and 100%.'),
  uvIrradiation: yup
    .number()
    .transform(nanToNull)
    .nullable()
    .min(0, 'UV irradiation must be zero or greater.'),
  indoors: yup.boolean().defined(),
  changeOverTime: yup.boolean().defined(),
  durationOfDisturbance: yup
    .number()
    .transform(nanToNull)
    .nullable()
    .min(0, 'Duration of disturbance must be zero or greater.'),
  descriptionOfDisturbance: yup.string().nullable().defined(),
  geographicLocationCategoryId: yup.string().nullable().defined(),
})

const schema = yup.object({
  realistic: yup.boolean().defined(),
  scenarioCategoryId: yup.string().nullable().required('Please select a scenario category.'),
  persistencies: yup.array().of(persistenceSchema),
  contactTemplates: yup.array().of(
    yup.object({
      duration: yup.number().transform(nanToNull).nullable().min(0, 'Duration must be zero or greater.'),
      contactArea: yup
        .number()
        .transform(nanToNull)
        .nullable()
        .min(0, 'Contact area must be zero or greater.'),
      temperature: yup.number().transform(nanToNull).nullable().defined(),
      humidity: yup
        .number()
        .transform(nanToNull)
        .nullable()
        .min(0, 'Humidity must be between 0 and 100%.')
        .max(1, 'Humidity must be between 0 and 100%.'),
      uvIrradiation: yup
        .number()
        .transform(nanToNull)
        .nullable()
        .min(0, 'UV irradiation must be zero or greater.'),
    }),
  ),
})

const { defineField, errors, handleSubmit, setValues, values, resetForm } = useForm<ScenarioFormValues>({
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

const studyScenarios = ref<Scenario[]>([])
const studyScenariosLoading = ref(false)
const persistencePickerVisible = ref(false)

// The picker browses this study's scenarios, then the persistencies on
// whichever one is opened - only those already belonging to this study, and
// not already used on the current draft, since picking one duplicates it
// below (so editing the copy never silently changes another scenario's
// data).
const pickableScenarios = computed(() => {
  const usedIds = new Set(values.persistencies.map((p) => p.id).filter((id): id is string => !!id))
  return studyScenarios.value
    .filter((scenario) => scenario.id !== editingId.value)
    .map((scenario) => ({
      ...scenario,
      persistencies: scenario.persistencies.filter(
        (p) => p.owning_study_id === studyId.value && !usedIds.has(p.id),
      ),
    }))
})

const hasPickablePersistencies = computed(() =>
  pickableScenarios.value.some((scenario) => scenario.persistencies.length > 0),
)

// Keeps an in-progress edit recoverable across an accidental reload/close of
// the tab. Scoped per study + which scenario is being edited/duplicated, so
// switching targets can't resurrect the wrong draft.
const draftStorageKey = computed(
  () => `transact.scenarioFormDraft.${studyId.value}.${editingId.value ?? duplicateFromId.value ?? 'new'}`,
)

interface ScenarioFormDraft {
  activeStep: string
  values: ScenarioFormValues
}

function readDraft(): ScenarioFormDraft | null {
  try {
    const raw = localStorage.getItem(draftStorageKey.value)
    return raw ? (JSON.parse(raw) as ScenarioFormDraft) : null
  } catch {
    return null
  }
}

function writeDraft() {
  try {
    const draft: ScenarioFormDraft = { activeStep: activeStep.value, values }
    localStorage.setItem(draftStorageKey.value, JSON.stringify(draft))
  } catch {
    // Storage can be unavailable (private browsing) or full - losing
    // autosave isn't worth surfacing an error over.
  }
}

function clearDraft() {
  try {
    localStorage.removeItem(draftStorageKey.value)
  } catch {
    // Ignore - nothing to clean up if storage isn't available.
  }
}

// Debounced so fast typing doesn't hit localStorage on every keystroke. Only
// autosaves once the real data has loaded, so the draft can't be clobbered
// by the form's blank initial values while the network fetch is in flight.
let autosaveReady = false
watchDebounced(
  [values, activeStep],
  () => {
    if (autosaveReady && isEditable.value) writeDraft()
  },
  { debounce: 500, deep: true },
)

async function loadForm() {
  autosaveReady = false
  resetForm()
  activeStep.value = '1'
  loadError.value = ''
  submitError.value = ''
  owningStudyId.value = null
  collapsedContactTemplates.value = [false]

  studyScenariosLoading.value = true
  listScenarios()
    .then((data) => {
      studyScenarios.value = data.filter((scenario) =>
        scenario.studies.some((s) => s.id === studyId.value),
      )
    })
    .finally(() => (studyScenariosLoading.value = false))

  if (editingId.value !== null) {
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
      restoreDraftIfPresent()
    } catch {
      loadError.value = 'Could not load this scenario.'
    } finally {
      loading.value = false
      autosaveReady = true
    }
    return
  }

  if (duplicateFromId.value === null) {
    restoreDraftIfPresent()
    autosaveReady = true
    return
  }

  loading.value = true
  try {
    const scenario = await getScenario(duplicateFromId.value)
    const persistencies = scenario.persistencies
      .map((p) => clonePersistenceDraftForDuplication(persistenceDraftFromPersistence(p)))
    const contactTemplates = scenario.contact_templates.length
      ? scenario.contact_templates.map((template) =>
          cloneContactTemplateDraftForDuplication(contactTemplateDraftFromContactTemplate(template)),
        )
      : [emptyContactTemplateDraft()]
    setValues({
      realistic: !!scenario.realistic,
      scenarioCategoryId: scenario.scenario_category_id ?? null,
      persistencies,
      contactTemplates,
    })
    collapsedPersistencies.value = persistencies.map(() => true)
    collapsedContactTemplates.value = contactTemplates.map(
      () => scenario.contact_templates.length > 0,
    )
    restoreDraftIfPresent()
  } catch {
    loadError.value = 'Could not load the source scenario to duplicate.'
  } finally {
    loading.value = false
    autosaveReady = true
  }
}

// Overlays a locally-saved draft (if any) on top of the freshly-loaded
// baseline, so a reload or accidental close recovers unsaved edits instead
// of silently discarding them.
function restoreDraftIfPresent() {
  const draft = readDraft()
  if (!draft) return
  setValues(draft.values)
  activeStep.value = draft.activeStep
  collapsedPersistencies.value = draft.values.persistencies.map(() => true)
  collapsedContactTemplates.value = draft.values.contactTemplates.map(() => true)
  toast.add({
    color: 'info',
    title: 'Unsaved changes restored',
    description: 'We recovered a draft of this form from your last session.',
    duration: 5000,
  })
}

// Reload the form fresh each time the dialog opens, since the same instance
// is reused across "Add scenario" / "Edit" / "Duplicate" clicks.
watch(open, (isOpen) => {
  if (isOpen) loadForm()
  else autosaveReady = false
})

function addPersistence() {
  collapsedPersistencies.value = collapsedPersistencies.value.map(() => true)
  pushPersistence(emptyPersistenceDraft())
  collapsedPersistencies.value.push(false)
}

// Duplicated, not linked: this scenario gets its own independent copy, so
// editing it here can't silently change the persistence on another scenario
// that also uses it.
function addExistingPersistence(persistence: Persistence) {
  collapsedPersistencies.value = collapsedPersistencies.value.map(() => true)
  pushPersistence(clonePersistenceDraftForDuplication(persistenceDraftFromPersistence(persistence)))
  collapsedPersistencies.value.push(false)
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

// Copies this card's own values into a new card in the same scenario - a
// quick way to reuse one contact template as the starting point for a
// near-identical one, without round-tripping through another study.
function duplicateContactTemplate(index: number) {
  collapsedContactTemplates.value = collapsedContactTemplates.value.map(() => true)
  pushContactTemplate(
    cloneContactTemplateDraftForDuplication(contactTemplateFields.value[index]!.value),
  )
  collapsedContactTemplates.value.push(false)
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

// Jumps to whichever step/card holds the first validation error and expands
// it, so a field invalid on step 2/3 can't silently fail to save while the
// user is looking at (and only sees success/failure on) a different step.
function revealFirstError(errorPaths: string[]) {
  const path = errorPaths[0]
  if (!path) return

  const persistenceMatch = path.match(/^persistencies\[(\d+)\]/)
  if (persistenceMatch) {
    const index = Number(persistenceMatch[1])
    activeStep.value = stepToPanel.persistence
    if (collapsedPersistencies.value[index]) collapsedPersistencies.value[index] = false
    return
  }

  const contactTemplateMatch = path.match(/^contactTemplates\[(\d+)\]/)
  if (contactTemplateMatch) {
    const index = Number(contactTemplateMatch[1])
    activeStep.value = stepToPanel['contact-templates']
    if (collapsedContactTemplates.value[index]) collapsedContactTemplates.value[index] = false
    return
  }

  activeStep.value = stepToPanel.details
}

const onSubmit = handleSubmit(
  async (formValues) => {
    if (!isEditable.value) return

    const incomplete = firstIncompleteStep()
    if (incomplete) {
      activeStep.value = stepToPanel[incomplete.step]
      toast.add({ color: 'warning', title: 'Scenario incomplete', description: incomplete.message, duration: 5000 })
      return
    }

    await saveScenario(formValues)
  },
  ({ errors: validationErrors }) => {
    revealFirstError(Object.keys(validationErrors))
    toast.add({
      color: 'error',
      title: 'Scenario has errors',
      description: 'Please fix the highlighted fields before saving.',
      duration: 5000,
    })
  },
)

async function saveScenario(formValues: ScenarioFormValues) {
  submitting.value = true
  submitError.value = ''
  try {
    const persistenceIds: string[] = []
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

    const contactTemplateIds: string[] = []
    for (const contactTemplate of formValues.contactTemplates) {
      contactTemplateIds.push(await saveContactTemplateDraft(contactTemplate, scenario.id))
    }
    await updateScenario(scenario.id, { contact_template_ids: contactTemplateIds })

    clearDraft()
    open.value = false
    emit('saved')
  } catch {
    submitError.value = 'Could not save the scenario. Please try again.'
  } finally {
    submitting.value = false
  }
}

function onCancel() {
  clearDraft()
  open.value = false
}

const title = computed(() =>
  editingId.value !== null ? 'Edit scenario' : duplicateFromId.value !== null ? 'Duplicate scenario' : 'Add scenario',
)
</script>

<template>
  <UModal
    v-model:open="open"
    :title="title"
    :ui="{
      content: 'max-w-3xl top-4 left-1/2 -translate-x-1/2 translate-y-0 h-[calc(100dvh-2rem)] max-h-[calc(100dvh-2rem)]',
      body: 'flex-1 overflow-y-auto',
    }"
  >
    <template #body>
      <UAlert
        v-if="duplicateFromId !== null && !loading && !loadError"
        color="info"
        variant="outline"
        description="Review and adjust the duplicated data below, then save to create it as a new scenario in this study."
        class="mb-4"
      />

      <div v-if="loading" class="flex justify-center py-12">
        <UProgress class="w-12" />
      </div>

      <UAlert v-else-if="loadError" color="error" variant="outline" :description="loadError" />

      <UAlert
        v-else-if="!isEditable"
        color="info"
        variant="outline"
        description="This scenario was created for another study, so it can only be edited there. You can still view it here, or remove it from this study on the scenarios list."
      />

      <form v-else id="scenario-form" class="flex flex-col gap-4" @submit.prevent="onSubmit">
        <UStepper
          v-model="activeStep"
          :items="stepItems"
          :linear="false"
          class="bg-transparent!"
        >
          <template #1>
            <div class="flex flex-col gap-4">
              <div class="flex flex-col gap-2">
                <CategorySelect
                  v-model="scenarioCategoryId"
                  label="Scenario category"
                  description="Use the label that you are also using in the sheet 'Activity Scenarios'. Provide the corresponding reference profiles in the sheet 'Reference Profiles'."
                  :api="scenarioCategoryApi"
                />
                <UAlert
                  v-if="errors.scenarioCategoryId"
                  color="error"
                  variant="subtle"
                  :description="errors.scenarioCategoryId"
                />
              </div>

              <div class="flex items-center gap-2">
                <USwitch v-model="realistic" id="realistic" />
                <label for="realistic" class="text-sm">Realistic scenario</label>
              </div>

              <div class="flex justify-end mt-2">
                <UButton label="Continue" trailing-icon="i-lucide-arrow-right" @click="activeStep = '2'" />
              </div>
            </div>
          </template>

          <template #2>
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

              <div class="flex gap-2">
                <UButton
                  label="Add new persistence"
                  icon="i-lucide-plus"
                  variant="outline"
                  @click="addPersistence"
                />
                <UButton
                  label="Duplicate a persistence from this study"
                  icon="i-lucide-copy"
                  variant="outline"
                  :loading="studyScenariosLoading"
                  :disabled="!hasPickablePersistencies"
                  @click="persistencePickerVisible = true"
                />
              </div>

              <PersistencePickerDialog
                v-model:visible="persistencePickerVisible"
                :scenarios="pickableScenarios"
                @select="addExistingPersistence"
              />

              <div class="flex justify-between mt-2">
                <UButton label="Back" icon="i-lucide-arrow-left" variant="ghost" @click="activeStep = '1'" />
                <UButton
                  label="Continue"
                  trailing-icon="i-lucide-arrow-right"
                  @click="activeStep = '3'"
                />
              </div>
            </div>
          </template>

          <template #3>
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
                @duplicate="duplicateContactTemplate(index)"
              />

              <UButton
                label="Add contact template"
                icon="i-lucide-plus"
                variant="outline"
                class="self-start"
                @click="addContactTemplate"
              />

              <div class="flex justify-start mt-2">
                <UButton label="Back" icon="i-lucide-arrow-left" variant="ghost" @click="activeStep = '2'" />
              </div>
            </div>
          </template>
        </UStepper>
      </form>
    </template>

    <template v-if="!loading && !loadError && isEditable" #footer>
      <div class="flex flex-col gap-2 w-full">
        <UAlert v-if="submitError" color="error" variant="outline" :description="submitError" />

        <div class="flex justify-end gap-2">
          <UButton label="Cancel" icon="i-lucide-x" variant="ghost" type="button" @click="onCancel" />
          <UButton
            type="submit"
            form="scenario-form"
            :icon="editingId === null ? 'i-lucide-plus' : 'i-lucide-save'"
            :label="editingId === null ? 'Add scenario' : 'Save changes'"
            :loading="submitting"
          />
        </div>
      </div>
    </template>
  </UModal>
</template>
