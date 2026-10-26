<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useFieldArray, useForm } from 'vee-validate'
import * as yup from 'yup'
import type { StepperItem } from '@nuxt/ui'
import { useConfirm } from '@/composables/useConfirm'
import { createStudy, deleteStudy, getStudy, updateStudy } from '@/api/studies'
import { useAuthStore } from '@/stores/auth'
import ScenariosList from '@/components/scenarios/ScenariosList.vue'
import DataEntryView from '@/views/data/DataEntryView.vue'
import type { StudyCreate, StudyUpdate } from '@/api/types'

const props = defineProps<{ id?: string }>()

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const confirm = useConfirm()

const editingId = computed(() => props.id ?? null)
const loadingStudy = ref(false)
const loadError = ref('')

// Which step to open, e.g. from the study list card's "Plan" / "Add data"
// buttons deep-linking via ?step=planning or ?step=data-entry. Kept in sync
// both ways: the URL seeds the initial step (so reloading or sharing a link
// re-opens the same step), and switching steps in the UI updates the URL.
const validSteps = ['details', 'planning', 'data-entry'] as const
type StepName = (typeof validSteps)[number]
const stepToPanel: Record<StepName, string> = { details: '1', planning: '2', 'data-entry': '3' }
const panelToStep: Record<string, StepName> = { '1': 'details', '2': 'planning', '3': 'data-entry' }

function stepFromQuery(): StepName {
  const step = route.query.step
  if (step === 'data-entry' && purpose.value !== 'repository') return 'details'
  return (validSteps as readonly string[]).includes(step as string) ? (step as StepName) : 'details'
}

const activeStep = computed<string>({
  get: () => stepToPanel[stepFromQuery()],
  set: (value) => {
    router.replace({ query: { ...route.query, step: panelToStep[value] ?? 'details' } })
  },
})

const stepItems = computed<StepperItem[]>(() => [
  { value: '1', title: 'Study details', slot: '1' },
  { value: '2', title: 'Planning', disabled: editingId.value === null, slot: '2' },
  ...(purpose.value === 'repository'
    ? [{ value: '3', title: 'Add data', disabled: editingId.value === null, slot: '3' }]
    : []),
])

const authorTitleOptions = ['Dr.', 'Prof.', 'Prof. Dr.']

const purposeOptions: { label: string; value: 'transfer' | 'repository' }[] = [
  { label: 'Plan a transfer experiment', value: 'transfer' },
  { label: 'Add data to repository', value: 'repository' },
]

interface AuthorFormValue {
  title: string | null
  first_name: string
  last_name: string
}

function emptyAuthor(): AuthorFormValue {
  return { title: null, first_name: '', last_name: '' }
}

function formatAuthorName(author: AuthorFormValue): string {
  return [author.title, author.first_name, author.last_name].filter(Boolean).join(' ').trim()
}

function authorHasName(author: AuthorFormValue): boolean {
  return !!author.first_name.trim() && !!author.last_name.trim()
}

const authorSchema = yup.object({
  title: yup.string().trim().nullable().defined(),
  first_name: yup.string().trim().required('First name is required.'),
  last_name: yup.string().trim().required('Last name is required.'),
})

const schema = yup.object({
  title: yup.string().trim().required('Title is required.'),
  doi: yup.string().trim().defined(),
  journal: yup.string().trim().defined(),
  year: yup
    .number()
    .nullable()
    .transform((value, original) => (original === '' || original == null ? null : value))
    .typeError('Year must be a number.')
    .test(
      'four-digits',
      'Year must be a 4-digit number.',
      (value) => value == null || (value >= 1000 && value <= 9999),
    ),
  abstract: yup.string().trim().defined(),
  description: yup.string().trim().defined(),
  authors: yup.array().of(authorSchema).min(1, 'Please add at least one author.'),
  correspondingAuthorIndex: yup.number().nullable().defined(),
  corresponding_author_email: yup
    .string()
    .trim()
    .email('Please enter a valid email address.')
    .defined(),
  purpose: yup
    .string()
    .nullable()
    .required('Please choose either "Plan a transfer experiment" or "Add data to repository".'),
  quality_check_passed: yup.boolean().defined(),
})

const { defineField, errors, handleSubmit, setValues, submitCount } = useForm({
  validationSchema: schema,
  initialValues: {
    title: '',
    doi: '',
    journal: '',
    year: null as number | null,
    abstract: '',
    description: '',
    authors: [emptyAuthor()],
    correspondingAuthorIndex: null as number | null,
    corresponding_author_email: '',
    purpose: null as 'transfer' | 'repository' | null,
    quality_check_passed: false,
  },
})

const [title, titleAttrs] = defineField('title')
const [doi, doiAttrs] = defineField('doi')
const [journal, journalAttrs] = defineField('journal')
const [year, yearAttrs] = defineField('year')
const [abstractField, abstractAttrs] = defineField('abstract')
const [description, descriptionAttrs] = defineField('description')
const [correspondingAuthorIndex] = defineField('correspondingAuthorIndex')
const [correspondingEmail, correspondingEmailAttrs] = defineField('corresponding_author_email')
const [purpose] = defineField('purpose')

const {
  fields: authorFields,
  push: pushAuthor,
  remove: removeAuthorField,
} = useFieldArray<AuthorFormValue>('authors')

function addAuthor() {
  pushAuthor(emptyAuthor())
}

function removeAuthor(index: number) {
  removeAuthorField(index)
  if (correspondingAuthorIndex.value === index) {
    clearCorrespondingAuthor()
  } else if (
    correspondingAuthorIndex.value !== null &&
    correspondingAuthorIndex.value !== undefined &&
    correspondingAuthorIndex.value > index
  ) {
    correspondingAuthorIndex.value -= 1
  }
}

// Only authors with both a first and last name can be picked as the
// corresponding author - a blank/half-filled row isn't a real author yet.
const correspondingAuthorOptions = computed(() =>
  authorFields.value
    .map((field, index) => ({ field, index }))
    .filter(({ field }) => authorHasName(field.value))
    .map(({ field, index }) => ({
      label: formatAuthorName(field.value),
      value: index,
    })),
)

function clearCorrespondingAuthor() {
  correspondingAuthorIndex.value = null
  correspondingEmail.value = ''
}

function onCorrespondingAuthorChange(value: number | null) {
  if (value === null) {
    clearCorrespondingAuthor()
  }
}

// If the row backing the selected corresponding author stops qualifying
// (e.g. its name gets cleared), drop the now-invalid selection.
watch(correspondingAuthorOptions, (options) => {
  if (
    correspondingAuthorIndex.value !== null &&
    correspondingAuthorIndex.value !== undefined &&
    !options.some((option) => option.value === correspondingAuthorIndex.value)
  ) {
    clearCorrespondingAuthor()
  }
})

function showAuthorError(index: number, field: 'first_name' | 'last_name'): string | undefined {
  if (!submitCount.value) return undefined
  return errors.value[`authors[${index}].${field}`]
}

onMounted(async () => {
  if (editingId.value === null) {
    const queryPurpose = route.query.purpose
    if (queryPurpose !== 'transfer' && queryPurpose !== 'repository') {
      router.replace({ name: 'studies-laboratory' })
      return
    }
    purpose.value = queryPurpose
    return
  }

  loadingStudy.value = true
  try {
    const study = await getStudy(editingId.value)
    const authors = study.authors.length
      ? study.authors.map((author) => ({
          title: author.title ?? null,
          first_name: author.first_name,
          last_name: author.last_name,
        }))
      : [emptyAuthor()]
    const correspondingIndex = study.corresponding_author_name
      ? authors.findIndex((author) => formatAuthorName(author) === study.corresponding_author_name)
      : -1
    setValues({
      title: study.title ?? '',
      doi: study.doi ?? '',
      journal: study.journal ?? '',
      year: study.year ? Number(study.year) : null,
      abstract: study.abstract ?? '',
      description: study.description ?? '',
      authors,
      correspondingAuthorIndex: correspondingIndex >= 0 ? correspondingIndex : null,
      corresponding_author_email: study.corresponding_author_email ?? '',
      purpose: study.plan_a_transfer_experiment
        ? 'transfer'
        : study.add_data_to_repository
          ? 'repository'
          : null,
      quality_check_passed: !!study.quality_check_passed,
    })
  } catch {
    loadError.value = 'Could not load this study.'
  } finally {
    loadingStudy.value = false
  }
})

const submitting = ref(false)
const submitError = ref('')

const continueAfterSubmit = ref(false)

const onSubmit = handleSubmit(async (values) => {
  submitting.value = true
  submitError.value = ''
  try {
    const correspondingAuthor =
      values.correspondingAuthorIndex != null
        ? values.authors[values.correspondingAuthorIndex]
        : undefined

    const shared = {
      title: values.title.trim(),
      doi: values.doi.trim() || null,
      journal: values.journal.trim() || null,
      year: values.year != null ? String(values.year) : null,
      abstract: values.abstract.trim() || null,
      description: values.description.trim() || null,
      corresponding_author_name: correspondingAuthor
        ? formatAuthorName(correspondingAuthor) || null
        : null,
      corresponding_author_email: values.corresponding_author_email.trim() || null,
      plan_a_transfer_experiment: values.purpose === 'transfer',
      add_data_to_repository: values.purpose === 'repository',
      quality_check_passed: values.quality_check_passed,
      authors: values.authors.map((author) => ({
        title: author.title?.trim() || null,
        first_name: author.first_name.trim(),
        last_name: author.last_name.trim(),
      })),
    }

    if (editingId.value === null) {
      const payload: StudyCreate = { ...shared, laboratory_id: auth.user!.laboratory_id! }
      const created = await createStudy(payload)
      router.push({ name: 'studies-edit', params: { id: created.id }, query: { step: 'planning' } })
    } else {
      const payload: StudyUpdate = shared
      await updateStudy(editingId.value, payload)
      if (continueAfterSubmit.value) {
        activeStep.value = '2'
      } else {
        router.push({ name: 'studies-laboratory' })
      }
    }
  } catch (error) {
    console.error(error)
    submitError.value = 'Could not save the study. Please try again.'
  } finally {
    submitting.value = false
    continueAfterSubmit.value = false
  }
})

function onSaveAndContinue() {
  continueAfterSubmit.value = true
  onSubmit()
}

function onCancel() {
  router.push({ name: 'studies-laboratory' })
}

const switchingPurpose = ref(false)
const switchPurposeError = ref('')

const otherPurposeOption = computed(() =>
  purposeOptions.find((option) => option.value !== purpose.value),
)

async function switchPurpose(newPurpose: 'transfer' | 'repository') {
  if (editingId.value === null) return
  switchingPurpose.value = true
  switchPurposeError.value = ''
  try {
    await updateStudy(editingId.value, {
      plan_a_transfer_experiment: newPurpose === 'transfer',
      add_data_to_repository: newPurpose === 'repository',
    })
    purpose.value = newPurpose
  } catch {
    switchPurposeError.value = 'Could not switch the study purpose. Please try again.'
  } finally {
    switchingPurpose.value = false
  }
}

function confirmSwitchPurpose(newPurpose: 'transfer' | 'repository') {
  if (newPurpose === purpose.value) return
  const label = purposeOptions.find((option) => option.value === newPurpose)?.label ?? newPurpose
  confirm.require({
    message: `Switch this study's purpose to "${label}"?`,
    header: 'Switch study purpose',
    rejectLabel: 'Cancel',
    acceptLabel: 'Switch',
    acceptColor: 'error',
    accept: () => switchPurpose(newPurpose),
  })
}

const deleting = ref(false)
const deleteError = ref('')

async function removeStudy() {
  if (editingId.value === null) return
  deleting.value = true
  deleteError.value = ''
  try {
    await deleteStudy(editingId.value)
    router.push({ name: 'studies-laboratory' })
  } catch {
    deleteError.value = 'Could not delete this study. Please try again.'
  } finally {
    deleting.value = false
  }
}

function confirmDeleteStudy() {
  confirm.require({
    message: 'Delete this study permanently? This cannot be undone.',
    header: 'Delete study',
    rejectLabel: 'Cancel',
    acceptLabel: 'Delete',
    acceptColor: 'error',
    accept: removeStudy,
  })
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <h1 v-if="editingId === null" class="text-2xl font-bold text-surface-900 dark:text-surface-0">
      {{ purposeOptions.find((option) => option.value === purpose)?.label ?? 'Add study' }}
    </h1>

    <div v-if="loadingStudy" class="flex justify-center py-12">
      <UProgress class="w-12" />
    </div>

    <UAlert v-else-if="loadError" color="error" variant="outline" :description="loadError" />

    <UStepper
      v-else
      v-model="activeStep"
      :items="stepItems"
      :linear="false"
      class="bg-transparent!"
    >
        <template #1>
          <form class="flex flex-col gap-4 max-w-2xl" @submit.prevent="onSubmit">
            <UFormField label="Title" :error="errors.title">
              <UInput
                id="study-title"
                v-model="title"
                v-bind="titleAttrs"
                class="w-full"
                autofocus
              />
            </UFormField>

            <UFormField label="Description" hint="Optional">
              <UTextarea
                id="study-description"
                v-model="description"
                v-bind="descriptionAttrs"
                :rows="3"
                class="w-full"
              />
            </UFormField>

            <div class="flex flex-col gap-2">
              <div class="flex items-center justify-between">
                <label class="font-medium text-sm">Authors</label>
                <UButton label="Add author" icon="i-lucide-plus" variant="ghost" size="sm" @click="addAuthor" />
              </div>
              <div
                v-for="(field, index) in authorFields"
                :key="field.key"
                class="flex flex-col sm:flex-row gap-2 sm:items-start"
              >
                <USelectMenu
                  v-model="field.value.title"
                  :items="authorTitleOptions"
                  placeholder="Title"
                  clear
                  class="w-full sm:w-28 sm:shrink-0"
                />
                <UFormField class="flex-1" :error="showAuthorError(index, 'first_name')">
                  <UInput
                    v-model="field.value.first_name"
                    placeholder="First name"
                    class="w-full"
                  />
                </UFormField>
                <UFormField class="flex-1" :error="showAuthorError(index, 'last_name')">
                  <UInput
                    v-model="field.value.last_name"
                    placeholder="Last name"
                    class="w-full"
                  />
                </UFormField>
                <UButton
                  icon="i-lucide-trash-2"
                  color="error"
                  variant="ghost"
                  aria-label="Remove author"
                  :disabled="authorFields.length === 1"
                  @click="removeAuthor(index)"
                />
              </div>
            </div>

            <template v-if="purpose === 'repository'">
              <UFormField label="Journal" hint="Optional">
                <UInput id="study-journal" v-model="journal" v-bind="journalAttrs" class="w-full" />
              </UFormField>

              <div class="grid grid-cols-2 gap-4">
                <UFormField label="Year" hint="Optional" :error="errors.year">
                  <!-- TODO: number formatting (was :use-grouping="false") -->
                  <UInputNumber
                    id="study-year"
                    v-model="year"
                    v-bind="yearAttrs"
                    :min="1000"
                    :max="9999"
                    orientation="vertical"
                    class="w-full"
                  />
                </UFormField>
                <UFormField label="DOI" hint="Optional">
                  <UInput id="study-doi" v-model="doi" v-bind="doiAttrs" class="w-full" />
                </UFormField>
              </div>

              <UFormField label="Abstract" hint="Optional">
                <UTextarea
                  id="study-abstract"
                  v-model="abstractField"
                  v-bind="abstractAttrs"
                  :rows="3"
                  class="w-full"
                />
              </UFormField>
            </template>

            <UFormField label="Corresponding author contact" hint="Optional">
              <USelectMenu
                id="study-contact-author"
                v-model="correspondingAuthorIndex"
                :items="correspondingAuthorOptions"
                :placeholder="
                  correspondingAuthorOptions.length
                    ? 'Select an author'
                    : 'Add an author with a first and last name first'
                "
                :disabled="!correspondingAuthorOptions.length"
                clear
                class="w-full"
                @update:model-value="onCorrespondingAuthorChange"
              />
            </UFormField>

            <UFormField label="Email" hint="Optional" :error="errors.corresponding_author_email">
              <UInput
                id="study-contact-email"
                v-model="correspondingEmail"
                v-bind="correspondingEmailAttrs"
                :disabled="correspondingAuthorIndex == null"
                type="email"
                class="w-full"
              />
            </UFormField>

            <UAlert v-if="submitError" color="error" variant="outline" :description="submitError" />

            <div v-if="editingId !== null" class="flex justify-end mt-2">
              <UButton
                label="Save & continue"
                trailing-icon="i-lucide-arrow-right"
                variant="ghost"
                type="button"
                :loading="submitting && continueAfterSubmit"
                @click="onSaveAndContinue"
              />
            </div>

            <div class="flex gap-2 mt-4">
              <UButton
                type="submit"
                :icon="editingId === null ? undefined : 'i-lucide-save'"
                :trailing-icon="editingId === null ? 'i-lucide-arrow-right' : undefined"
                :label="editingId === null ? 'Add study & continue' : 'Save changes'"
                :loading="submitting"
              />
              <UButton
                label="Cancel"
                icon="i-lucide-x"
                variant="ghost"
                type="button"
                @click="onCancel"
              />
            </div>
          </form>

          <template v-if="editingId !== null">
            <div class="max-w-2xl pt-16">
              <div class="flex items-center gap-2 mb-3">
                <UIcon name="i-lucide-triangle-alert" class="text-error size-4" />
                <h2 class="text-sm font-semibold text-error">Danger zone</h2>
              </div>

              <div class="rounded-lg border border-error/30 divide-y divide-error/20">
                <div class="flex items-center justify-between gap-4 p-4">
                  <div class="flex flex-col gap-1">
                    <span class="font-medium text-sm">Switch study purpose</span>
                    <p class="text-sm text-surface-500 dark:text-surface-400">
                      Currently
                      <span class="font-medium text-surface-700 dark:text-surface-200">{{
                        purposeOptions.find((option) => option.value === purpose)?.label
                      }}</span>. This affects how this study is used elsewhere.
                    </p>
                    <UAlert
                      v-if="switchPurposeError"
                      color="error"
                      variant="subtle"
                      :description="switchPurposeError"
                      class="mt-1"
                    />
                  </div>
                  <UButton
                    v-if="otherPurposeOption"
                    type="button"
                    icon="i-lucide-repeat"
                    :label="`Switch to: ${otherPurposeOption.label}`"
                    color="neutral"
                    variant="outline"
                    class="shrink-0"
                    :loading="switchingPurpose"
                    @click="confirmSwitchPurpose(otherPurposeOption.value)"
                  />
                </div>

                <div class="flex items-center justify-between gap-4 p-4">
                  <div class="flex flex-col gap-1">
                    <span class="font-medium text-sm">Delete study</span>
                    <p class="text-sm text-surface-500 dark:text-surface-400">
                      This action is permanent and cannot be undone.
                    </p>
                    <UAlert
                      v-if="deleteError"
                      color="error"
                      variant="subtle"
                      :description="deleteError"
                      class="mt-1"
                    />
                  </div>
                  <UButton
                    label="Delete"
                    icon="i-lucide-trash-2"
                    color="error"
                    class="shrink-0"
                    :loading="deleting"
                    @click="confirmDeleteStudy"
                  />
                </div>
              </div>
            </div>
          </template>
        </template>

        <template #2>
          <div v-if="editingId !== null" class="flex justify-end mb-2">
            <UButton
              label="Print planning checklist"
              icon="i-lucide-printer"
              variant="outline"
              size="sm"
              @click="router.push({ name: 'studies-checklist', params: { id: editingId } })"
            />
          </div>
          <ScenariosList v-if="editingId !== null" :study-id="editingId" />
          <div class="flex justify-between mt-4">
            <UButton label="Previous step" icon="i-lucide-arrow-left" variant="ghost" type="button" @click="activeStep = '1'" />
            <UButton
              v-if="purpose === 'repository'"
              label="Next step"
              trailing-icon="i-lucide-arrow-right"
              variant="ghost"
              type="button"
              @click="activeStep = '3'"
            />
          </div>
        </template>

        <template v-if="purpose === 'repository'" #3>
          <DataEntryView v-if="editingId !== null" :study-id="String(editingId)" />
          <div class="flex justify-start mt-4">
            <UButton label="Previous step" icon="i-lucide-arrow-left" variant="ghost" type="button" @click="activeStep = '2'" />
          </div>
        </template>
    </UStepper>
  </div>
</template>
