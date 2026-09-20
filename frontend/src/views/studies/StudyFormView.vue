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

const authorTitleOptions = ['Dr.', 'Prof.', 'Prof. Dr.', 'PhD', 'MSc', 'BSc']

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
  corresponding_author_phone: yup.string().trim().defined(),
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
    corresponding_author_phone: '',
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
const [correspondingPhone, correspondingPhoneAttrs] = defineField('corresponding_author_phone')
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
  correspondingPhone.value = ''
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
      corresponding_author_phone: study.corresponding_author_phone ?? '',
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
      corresponding_author_phone: values.corresponding_author_phone.trim() || null,
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
      router.push({ name: 'studies-laboratory' })
    }
  } catch {
    submitError.value = 'Could not save the study. Please try again.'
  } finally {
    submitting.value = false
  }
})

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
            <div class="flex flex-col gap-2">
              <label for="study-title" class="font-medium text-sm">Title</label>
              <UInput
                id="study-title"
                v-model="title"
                v-bind="titleAttrs"
                :color="errors.title ? 'error' : undefined"
                class="w-full"
                autofocus
              />
              <UAlert v-if="errors.title" color="error" variant="subtle" :description="errors.title" />
            </div>

            <div class="flex flex-col gap-2">
              <label for="study-description" class="font-medium text-sm"
                >Description (Optional)</label
              >
              <UTextarea
                id="study-description"
                v-model="description"
                v-bind="descriptionAttrs"
                :rows="3"
                class="w-full"
              />
            </div>

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
                <div class="flex-1 flex flex-col gap-1">
                  <UInput
                    v-model="field.value.first_name"
                    placeholder="First name"
                    :color="showAuthorError(index, 'first_name') ? 'error' : undefined"
                    class="w-full"
                  />
                  <UAlert
                    v-if="showAuthorError(index, 'first_name')"
                    color="error"
                    variant="subtle"
                    :description="showAuthorError(index, 'first_name')"
                  />
                </div>
                <div class="flex-1 flex flex-col gap-1">
                  <UInput
                    v-model="field.value.last_name"
                    placeholder="Last name"
                    :color="showAuthorError(index, 'last_name') ? 'error' : undefined"
                    class="w-full"
                  />
                  <UAlert
                    v-if="showAuthorError(index, 'last_name')"
                    color="error"
                    variant="subtle"
                    :description="showAuthorError(index, 'last_name')"
                  />
                </div>
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
              <div class="flex flex-col gap-2">
                <label for="study-journal" class="font-medium text-sm">Journal (Optional)</label>
                <UInput id="study-journal" v-model="journal" v-bind="journalAttrs" class="w-full" />
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div class="flex flex-col gap-2">
                  <label for="study-year" class="font-medium text-sm">Year (Optional)</label>
                  <!-- TODO: number formatting (was :use-grouping="false") -->
                  <UInputNumber
                    id="study-year"
                    v-model="year"
                    v-bind="yearAttrs"
                    :color="errors.year ? 'error' : undefined"
                    :min="1000"
                    :max="9999"
                    class="w-full"
                  />
                  <UAlert v-if="errors.year" color="error" variant="subtle" :description="errors.year" />
                </div>
                <div class="flex flex-col gap-2">
                  <label for="study-doi" class="font-medium text-sm">DOI (Optional)</label>
                  <UInput id="study-doi" v-model="doi" v-bind="doiAttrs" class="w-full" />
                </div>
              </div>

              <div class="flex flex-col gap-2">
                <label for="study-abstract" class="font-medium text-sm">Abstract (Optional)</label>
                <UTextarea
                  id="study-abstract"
                  v-model="abstractField"
                  v-bind="abstractAttrs"
                  :rows="3"
                  class="w-full"
                />
              </div>
            </template>

            <div class="flex flex-col gap-2">
              <label for="study-contact-author" class="font-medium text-sm"
                >Corresponding author contact (Optional)</label
              >
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
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="flex flex-col gap-2">
                <label for="study-contact-email" class="font-medium text-sm"
                  >Email (Optional)</label
                >
                <UInput
                  id="study-contact-email"
                  v-model="correspondingEmail"
                  v-bind="correspondingEmailAttrs"
                  :color="errors.corresponding_author_email ? 'error' : undefined"
                  :disabled="correspondingAuthorIndex == null"
                  type="email"
                  class="w-full"
                />
                <UAlert
                  v-if="errors.corresponding_author_email"
                  color="error"
                  variant="subtle"
                  :description="errors.corresponding_author_email"
                />
              </div>
              <div class="flex flex-col gap-2">
                <label for="study-contact-phone" class="font-medium text-sm"
                  >Phone number (Optional)</label
                >
                <UInput
                  id="study-contact-phone"
                  v-model="correspondingPhone"
                  v-bind="correspondingPhoneAttrs"
                  :disabled="correspondingAuthorIndex == null"
                  class="w-full"
                />
              </div>
            </div>

            <UAlert v-if="submitError" color="error" variant="outline" :description="submitError" />

            <div class="flex justify-between items-center gap-2 mt-2">
              <div class="flex gap-2">
                <UButton
                  type="submit"
                  :label="editingId === null ? 'Add study & continue' : 'Save changes'"
                  :loading="submitting"
                />
                <UButton label="Cancel" variant="ghost" type="button" @click="onCancel" />
              </div>
              <UButton
                v-if="editingId !== null"
                label="Continue"
                trailing-icon="i-lucide-arrow-right"
                variant="ghost"
                type="button"
                @click="activeStep = '2'"
              />
            </div>
          </form>

          <template v-if="editingId !== null">
            <div class="max-w-2xl pt-16">
              <USeparator />
            </div>

            <div class="max-w-2xl flex flex-col gap-4">
              <div>
                <h2 class="text-lg font-semibold text-red-700 dark:text-red-400">Danger zone</h2>
                <p class="text-sm text-surface-500 dark:text-surface-400">
                  These actions are irreversible or affect how this study is used elsewhere.
                </p>
              </div>

              <div class="flex flex-col gap-2">
                <label class="font-medium text-sm">Switch study purpose</label>
                <p class="text-sm text-surface-500 dark:text-surface-400">
                  Currently:
                  <span class="font-medium text-surface-700 dark:text-surface-200">{{
                    purposeOptions.find((option) => option.value === purpose)?.label
                  }}</span>
                </p>
                <UButton
                  v-if="otherPurposeOption"
                  type="button"
                  :label="`Switch to: ${otherPurposeOption.label}`"
                  color="neutral"
                  variant="outline"
                  class="w-fit"
                  :loading="switchingPurpose"
                  @click="confirmSwitchPurpose(otherPurposeOption.value)"
                />
                <UAlert
                  v-if="switchPurposeError"
                  color="error"
                  variant="subtle"
                  :description="switchPurposeError"
                />
              </div>

              <div class="flex flex-col gap-2">
                <label class="font-medium text-sm">Delete study</label>
                <UButton
                  label="Delete"
                  icon="i-lucide-trash-2"
                  color="error"
                  class="w-fit"
                  :loading="deleting"
                  @click="confirmDeleteStudy"
                />
                <UAlert
                  v-if="deleteError"
                  color="error"
                  variant="subtle"
                  :description="deleteError"
                />
              </div>
            </div>
          </template>
        </template>

        <template #2>
          <ScenariosList v-if="editingId !== null" :study-id="editingId" />
          <div class="flex justify-between mt-4">
            <UButton label="Back" icon="i-lucide-arrow-left" variant="ghost" type="button" @click="activeStep = '1'" />
            <UButton
              v-if="purpose === 'repository'"
              label="Continue"
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
            <UButton label="Back" icon="i-lucide-arrow-left" variant="ghost" type="button" @click="activeStep = '2'" />
          </div>
        </template>
    </UStepper>
  </div>
</template>
