<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useFieldArray, useForm } from 'vee-validate'
import * as yup from 'yup'
import {
  classificationCriteriaApi,
  classificationSchemeApi,
  determinationOfSheddingPropensityCategoryApi,
  monitoredTransferFactorApi,
  restrictionPriorToSamplingApi,
  shedderTestApi,
} from '@/api/categories'
import type { DeterminationOfSheddingPropensityCategory, NamedCategory } from '@/api/types'
import DurationValueInput from '@/components/scenarios/DurationValueInput.vue'
import { doiSchema, normalizeDoi } from '@/constants/doi'

const modelValue = defineModel<string | null>({ default: null })

const options = ref<DeterminationOfSheddingPropensityCategory[]>([])
const loading = ref(false)

function formatAuthors(option: DeterminationOfSheddingPropensityCategory): string {
  const authors = option.authors ?? []
  if (!authors.length) return ''
  const first = authors[0]!.last_name
  return authors.length > 1 ? `${first} et al.` : first
}

// These records don't have a "name" - label them by title, falling back to
// authors or the record id so every option in the dropdown is identifiable.
const selectOptions = computed(() =>
  options.value.map((option) => ({
    id: option.id,
    label: option.title || formatAuthors(option) || `Reference #${option.id}`,
  })),
)

async function load() {
  loading.value = true
  try {
    options.value = await determinationOfSheddingPropensityCategoryApi.list()
  } finally {
    loading.value = false
  }
}

onMounted(load)

// Lookup lists for the add dialog. Only superusers can add entries to them,
// so they are offered as fixed choices.
const restrictionOptions = ref<NamedCategory[]>([])
const shedderTestOptions = ref<NamedCategory[]>([])
const transferFactorOptions = ref<NamedCategory[]>([])
const criteriaOptions = ref<NamedCategory[]>([])
const schemeOptions = ref<NamedCategory[]>([])
const lookupsLoading = ref(false)
let lookupsLoaded = false

async function loadLookups() {
  if (lookupsLoaded) return
  lookupsLoading.value = true
  try {
    const [restrictions, shedderTests, transferFactors, criteria, schemes] = await Promise.all([
      restrictionPriorToSamplingApi.list(),
      shedderTestApi.list(),
      monitoredTransferFactorApi.list(),
      classificationCriteriaApi.list(),
      classificationSchemeApi.list(),
    ])
    restrictionOptions.value = restrictions
    shedderTestOptions.value = shedderTests
    transferFactorOptions.value = transferFactors
    criteriaOptions.value = criteria
    schemeOptions.value = schemes
    lookupsLoaded = true
  } finally {
    lookupsLoading.value = false
  }
}

const authorTitleOptions = ['Dr.', 'Prof.', 'Prof. Dr.']

interface AuthorFormValue {
  title: string | null
  first_name: string
  last_name: string
}

interface TimedEntryFormValue {
  id: string | null
  duration: number | null
}

interface FormState {
  title: string
  doi: string
  authors: AuthorFormValue[]
  restrictions: TimedEntryFormValue[]
  monitored_transfer_factor_ids: string[]
  number_of_participants: number | null
  replicates: number | null
  shedder_tests: TimedEntryFormValue[]
  classification_criteria_id: string | null
  classification_scheme_id: string | null
  classification_outcome: string
}

function emptyForm(): FormState {
  return {
    title: '',
    doi: '',
    authors: [],
    restrictions: [],
    monitored_transfer_factor_ids: [],
    number_of_participants: null,
    replicates: null,
    shedder_tests: [],
    classification_criteria_id: null,
    classification_scheme_id: null,
    classification_outcome: '',
  }
}

const timedEntrySchema = (message: string) =>
  yup.object({
    id: yup.string().nullable().required(message),
    duration: yup.number().nullable().defined(),
  })

const countSchema = yup
  .number()
  .nullable()
  .defined()
  .integer('Please enter a whole number.')
  .min(0, 'Please enter a positive number.')

// Either a title or an author identifies the reference - neither field is
// required on its own, but at least one of the two must be filled in.
const schema = yup
  .object({
    title: yup.string().trim().defined(),
    doi: doiSchema(),
    authors: yup
      .array(
        yup.object({
          title: yup.string().nullable().defined(),
          first_name: yup.string().trim().required('First name is required.'),
          last_name: yup.string().trim().required('Last name is required.'),
        }),
      )
      .defined(),
    restrictions: yup.array(timedEntrySchema('Please choose a restriction.')).defined(),
    monitored_transfer_factor_ids: yup.array(yup.string().defined()).defined(),
    number_of_participants: countSchema,
    replicates: countSchema,
    shedder_tests: yup.array(timedEntrySchema('Please choose a shedder test.')).defined(),
    classification_criteria_id: yup.string().nullable().defined(),
    classification_scheme_id: yup.string().nullable().defined(),
    classification_outcome: yup.string().trim().defined(),
  })
  .test(
    'authors-or-title',
    'Please provide at least a title or an author.',
    (values) => !!values.title?.trim() || values.authors.length > 0,
  )

const { defineField, errors, handleSubmit, resetForm, submitCount } = useForm<FormState>({
  validationSchema: schema,
  initialValues: emptyForm(),
})

const [title] = defineField('title')
const [doi] = defineField('doi')
const [monitoredTransferFactorIds] = defineField('monitored_transfer_factor_ids')
const [numberOfParticipants] = defineField('number_of_participants')
const [replicates] = defineField('replicates')
const [classificationCriteriaId] = defineField('classification_criteria_id')
const [classificationSchemeId] = defineField('classification_scheme_id')
const [classificationOutcome] = defineField('classification_outcome')

const {
  fields: authorFields,
  push: pushAuthor,
  remove: removeAuthor,
} = useFieldArray<AuthorFormValue>('authors')
const {
  fields: restrictionFields,
  push: pushRestriction,
  remove: removeRestriction,
} = useFieldArray<TimedEntryFormValue>('restrictions')
const {
  fields: shedderTestFields,
  push: pushShedderTest,
  remove: removeShedderTest,
} = useFieldArray<TimedEntryFormValue>('shedder_tests')

// Nested errors are keyed like "authors[0].first_name"; only show them once
// the user tried to save, so fresh empty rows don't start out red.
function rowError(path: string): string | undefined {
  if (!submitCount.value) return undefined
  return (errors.value as Record<string, string | undefined>)[path]
}

const showAddDialog = ref(false)
const saving = ref(false)
const saveError = ref('')

function openAddDialog() {
  resetForm({ values: emptyForm() })
  saveError.value = ''
  showAddDialog.value = true
  void loadLookups()
}

const saveNewOption = handleSubmit(async (values) => {
  saving.value = true
  saveError.value = ''
  try {
    const created = await determinationOfSheddingPropensityCategoryApi.create({
      title: values.title.trim() || null,
      doi: normalizeDoi(values.doi) || null,
      authors: values.authors.map((author) => ({
        title: author.title || null,
        first_name: author.first_name.trim(),
        last_name: author.last_name.trim(),
      })),
      restrictions: values.restrictions.map((entry) => ({
        restriction_prior_to_sampling_id: entry.id!,
        duration: entry.duration,
      })),
      monitored_transfer_factor_ids: values.monitored_transfer_factor_ids,
      number_of_participants: values.number_of_participants,
      replicates: values.replicates,
      shedder_tests: values.shedder_tests.map((entry) => ({
        shedder_test_id: entry.id!,
        duration: entry.duration,
      })),
      classification_criteria_id: values.classification_criteria_id,
      classification_scheme_id: values.classification_scheme_id,
      classification_outcome: values.classification_outcome.trim() || null,
    })
    options.value = [...options.value, created]
    modelValue.value = created.id
    showAddDialog.value = false
  } catch {
    saveError.value = 'Could not save this reference. Please try again.'
  } finally {
    saving.value = false
  }
})
</script>

<template>
  <div class="flex flex-col gap-2">
    <UFormField label="Determination of shedding propensity">
      <div class="flex gap-2">
        <USelectMenu
          v-model="modelValue"
          :items="selectOptions"
          label-key="label"
          value-key="id"
          placeholder="Select an option"
          :loading="loading"
          clear
          class="w-full"
          :ui="{
            base: 'h-auto',
            value: 'whitespace-normal text-left truncate-0 line-clamp-none',
            content: 'w-(--reka-combobox-trigger-width) min-w-fit max-w-md',
            itemLabel: 'whitespace-normal',
          }"
        />
        <UButton icon="i-lucide-plus" variant="ghost" aria-label="Add new reference" @click="openAddDialog" />
      </div>
    </UFormField>

    <UModal
      v-model:open="showAddDialog"
      title="Add determination of shedding propensity reference"
      :ui="{ content: 'max-w-2xl', footer: 'justify-end' }"
    >
      <template #body>
        <div class="flex flex-col gap-4">
          <UAlert
            v-if="errors['']"
            color="error"
            variant="subtle"
            :description="errors['']"
          />
          <UFormField label="Title">
            <UInput v-model="title" class="w-full" autofocus />
          </UFormField>

          <div class="flex flex-col gap-2">
            <div class="flex items-center justify-between">
              <span class="font-medium text-sm">Authors</span>
              <UButton
                label="Add author"
                icon="i-lucide-plus"
                variant="ghost"
                size="sm"
                @click="pushAuthor({ title: null, first_name: '', last_name: '' })"
              />
            </div>
            <div
              v-for="(field, index) in authorFields"
              :key="field.key"
              class="flex flex-col sm:flex-row gap-2 sm:items-start"
            >
              <USelectMenu
                v-model="field.value.title"
                :items="authorTitleOptions"
                :search-input="false"
                placeholder="Title"
                clear
                class="w-full sm:w-28 sm:shrink-0"
              />
              <UFormField class="flex-1" :error="rowError(`authors[${index}].first_name`)">
                <UInput v-model="field.value.first_name" placeholder="First name" class="w-full" />
              </UFormField>
              <UFormField class="flex-1" :error="rowError(`authors[${index}].last_name`)">
                <UInput v-model="field.value.last_name" placeholder="Last name" class="w-full" />
              </UFormField>
              <UButton
                icon="i-lucide-trash-2"
                color="error"
                variant="ghost"
                aria-label="Remove author"
                @click="removeAuthor(index)"
              />
            </div>
          </div>

          <UFormField label="DOI" hint="Optional" :error="errors.doi">
            <UInput v-model="doi" class="w-full" @blur="doi = normalizeDoi(doi ?? '')" />
          </UFormField>

          <div class="flex flex-col gap-2">
            <div class="flex items-center justify-between">
              <span class="font-medium text-sm">Restrictions prior to sampling</span>
              <UButton
                label="Add restriction"
                icon="i-lucide-plus"
                variant="ghost"
                size="sm"
                @click="pushRestriction({ id: null, duration: null })"
              />
            </div>
            <div
              v-for="(field, index) in restrictionFields"
              :key="field.key"
              class="flex flex-col gap-2 p-3 border border-default rounded-md"
            >
              <div class="flex gap-2 items-start">
                <UFormField class="flex-1" :error="rowError(`restrictions[${index}].id`)">
                  <USelectMenu
                    v-model="field.value.id"
                    :items="restrictionOptions"
                    label-key="name"
                    value-key="id"
                    placeholder="Choose a restriction"
                    :loading="lookupsLoading"
                    clear
                    class="w-full"
                  />
                </UFormField>
                <UButton
                  icon="i-lucide-trash-2"
                  color="error"
                  variant="ghost"
                  aria-label="Remove restriction"
                  @click="removeRestriction(index)"
                />
              </div>
              <UFormField label="Duration" hint="Optional">
                <DurationValueInput v-model="field.value.duration" :units="['days', 'hours', 'minutes']" />
              </UFormField>
            </div>
          </div>

          <UFormField label="Monitored transfer factors" hint="Optional">
            <USelectMenu
              v-model="monitoredTransferFactorIds"
              :items="transferFactorOptions"
              label-key="name"
              value-key="id"
              multiple
              placeholder="Choose factors"
              :loading="lookupsLoading"
              clear
              class="w-full"
            />
          </UFormField>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <UFormField label="Number of participants" hint="Optional" :error="errors.number_of_participants">
              <UInputNumber v-model="numberOfParticipants" :min="0" orientation="vertical" class="w-full" />
            </UFormField>
            <UFormField label="Replicates" hint="Optional" :error="errors.replicates">
              <UInputNumber v-model="replicates" :min="0" orientation="vertical" class="w-full" />
            </UFormField>
          </div>

          <div class="flex flex-col gap-2">
            <div class="flex items-center justify-between">
              <span class="font-medium text-sm">Shedder tests</span>
              <UButton
                label="Add shedder test"
                icon="i-lucide-plus"
                variant="ghost"
                size="sm"
                @click="pushShedderTest({ id: null, duration: null })"
              />
            </div>
            <div
              v-for="(field, index) in shedderTestFields"
              :key="field.key"
              class="flex flex-col gap-2 p-3 border border-default rounded-md"
            >
              <div class="flex gap-2 items-start">
                <UFormField class="flex-1" :error="rowError(`shedder_tests[${index}].id`)">
                  <USelectMenu
                    v-model="field.value.id"
                    :items="shedderTestOptions"
                    label-key="name"
                    value-key="id"
                    placeholder="Choose a shedder test"
                    :loading="lookupsLoading"
                    clear
                    class="w-full"
                  />
                </UFormField>
                <UButton
                  icon="i-lucide-trash-2"
                  color="error"
                  variant="ghost"
                  aria-label="Remove shedder test"
                  @click="removeShedderTest(index)"
                />
              </div>
              <UFormField label="Duration" hint="Optional">
                <DurationValueInput v-model="field.value.duration" :units="['hours', 'minutes', 'seconds']" />
              </UFormField>
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <UFormField label="Classification criteria" hint="Optional">
              <USelectMenu
                v-model="classificationCriteriaId"
                :items="criteriaOptions"
                label-key="name"
                value-key="id"
                placeholder="Select an option"
                :loading="lookupsLoading"
                clear
                class="w-full"
                :ui="{ content: 'min-w-fit max-w-md', itemLabel: 'whitespace-normal' }"
              />
            </UFormField>
            <UFormField label="Classification scheme" hint="Optional">
              <USelectMenu
                v-model="classificationSchemeId"
                :items="schemeOptions"
                label-key="name"
                value-key="id"
                placeholder="Select an option"
                :loading="lookupsLoading"
                clear
                class="w-full"
                :ui="{ content: 'min-w-fit max-w-md', itemLabel: 'whitespace-normal' }"
              />
            </UFormField>
          </div>
          <UFormField label="Classification outcome" hint="Optional">
            <UTextarea v-model="classificationOutcome" :rows="2" class="w-full" />
          </UFormField>
          <p v-if="saveError" class="text-sm text-red-500">{{ saveError }}</p>
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="showAddDialog = false" />
        <UButton label="Add" icon="i-lucide-plus" :loading="saving" @click="saveNewOption" />
      </template>
    </UModal>
  </div>
</template>
