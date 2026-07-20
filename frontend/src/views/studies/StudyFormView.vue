<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useFieldArray, useForm } from 'vee-validate'
import * as yup from 'yup'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import Button from 'primevue/button'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import { createStudy, getStudy, updateStudy } from '@/api/studies'
import { useAuthStore } from '@/stores/auth'
import ScenariosList from '@/components/scenarios/ScenariosList.vue'
import type { StudyCreate, StudyUpdate } from '@/api/types'

const props = defineProps<{ id?: string }>()

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const editingId = computed(() => (props.id ? Number(props.id) : null))
const loadingStudy = ref(false)
const loadError = ref('')

const authorTitleOptions = ['Dr.', 'Prof.', 'Prof. Dr.', 'PhD', 'MSc', 'BSc']

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
      await createStudy(payload)
    } else {
      const payload: StudyUpdate = shared
      await updateStudy(editingId.value, payload)
    }
    router.push({ name: 'studies-laboratory' })
  } catch {
    submitError.value = 'Could not save the study. Please try again.'
  } finally {
    submitting.value = false
  }
})

function onCancel() {
  router.push({ name: 'studies-laboratory' })
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <h1 v-if="editingId === null" class="text-2xl font-bold text-surface-900 dark:text-surface-0">
      Add study
    </h1>

    <div v-if="loadingStudy" class="flex justify-center py-12">
      <ProgressSpinner style="width: 3rem; height: 3rem" />
    </div>

    <Message v-else-if="loadError" severity="error" size="small">{{ loadError }}</Message>

    <Tabs v-else value="details">
      <TabList>
        <Tab value="details">Details</Tab>
        <Tab v-if="editingId !== null" value="scenarios">Scenarios</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="details">
          <form class="flex flex-col gap-4 max-w-2xl" @submit.prevent="onSubmit">
            <div class="flex flex-col gap-2">
              <label for="study-title" class="font-medium text-sm">Title</label>
              <InputText
                id="study-title"
                v-model="title"
                v-bind="titleAttrs"
                :invalid="!!errors.title"
                fluid
                autofocus
              />
              <Message v-if="errors.title" severity="error" size="small" variant="simple">
                {{ errors.title }}
              </Message>
            </div>

            <div class="flex flex-col gap-2">
              <label for="study-description" class="font-medium text-sm"
                >Description (Optional)</label
              >
              <Textarea
                id="study-description"
                v-model="description"
                v-bind="descriptionAttrs"
                rows="3"
                fluid
              />
            </div>

            <div class="flex flex-col gap-2">
              <div class="flex items-center justify-between">
                <label class="font-medium text-sm">Authors</label>
                <Button label="Add author" icon="pi pi-plus" text size="small" @click="addAuthor" />
              </div>
              <div
                v-for="(field, index) in authorFields"
                :key="field.key"
                class="flex flex-col sm:flex-row gap-2 sm:items-start"
              >
                <Select
                  v-model="field.value.title"
                  :options="authorTitleOptions"
                  placeholder="Title"
                  show-clear
                  class="w-full sm:w-28 sm:shrink-0"
                />
                <div class="flex-1 flex flex-col gap-1">
                  <InputText
                    v-model="field.value.first_name"
                    placeholder="First name"
                    :invalid="!!showAuthorError(index, 'first_name')"
                    fluid
                  />
                  <Message
                    v-if="showAuthorError(index, 'first_name')"
                    severity="error"
                    size="small"
                    variant="simple"
                  >
                    {{ showAuthorError(index, 'first_name') }}
                  </Message>
                </div>
                <div class="flex-1 flex flex-col gap-1">
                  <InputText
                    v-model="field.value.last_name"
                    placeholder="Last name"
                    :invalid="!!showAuthorError(index, 'last_name')"
                    fluid
                  />
                  <Message
                    v-if="showAuthorError(index, 'last_name')"
                    severity="error"
                    size="small"
                    variant="simple"
                  >
                    {{ showAuthorError(index, 'last_name') }}
                  </Message>
                </div>
                <Button
                  icon="pi pi-trash"
                  severity="danger"
                  text
                  aria-label="Remove author"
                  :disabled="authorFields.length === 1"
                  @click="removeAuthor(index)"
                />
              </div>
            </div>

            <template v-if="purpose === 'repository'">
              <div class="flex flex-col gap-2">
                <label for="study-journal" class="font-medium text-sm">Journal (Optional)</label>
                <InputText id="study-journal" v-model="journal" v-bind="journalAttrs" fluid />
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div class="flex flex-col gap-2">
                  <label for="study-year" class="font-medium text-sm">Year (Optional)</label>
                  <InputNumber
                    id="study-year"
                    v-model="year"
                    v-bind="yearAttrs"
                    :invalid="!!errors.year"
                    :use-grouping="false"
                    :min="1000"
                    :max="9999"
                    fluid
                  />
                  <Message v-if="errors.year" severity="error" size="small" variant="simple">
                    {{ errors.year }}
                  </Message>
                </div>
                <div class="flex flex-col gap-2">
                  <label for="study-doi" class="font-medium text-sm">DOI (Optional)</label>
                  <InputText id="study-doi" v-model="doi" v-bind="doiAttrs" fluid />
                </div>
              </div>

              <div class="flex flex-col gap-2">
                <label for="study-abstract" class="font-medium text-sm">Abstract (Optional)</label>
                <Textarea
                  id="study-abstract"
                  v-model="abstractField"
                  v-bind="abstractAttrs"
                  rows="3"
                  fluid
                />
              </div>
            </template>

            <div class="flex flex-col gap-2">
              <label for="study-contact-author" class="font-medium text-sm"
                >Corresponding author contact (Optional)</label
              >
              <Select
                id="study-contact-author"
                v-model="correspondingAuthorIndex"
                :options="correspondingAuthorOptions"
                option-label="label"
                option-value="value"
                :placeholder="
                  correspondingAuthorOptions.length
                    ? 'Select an author'
                    : 'Add an author with a first and last name first'
                "
                :disabled="!correspondingAuthorOptions.length"
                show-clear
                fluid
                @update:model-value="onCorrespondingAuthorChange"
              />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="flex flex-col gap-2">
                <label for="study-contact-email" class="font-medium text-sm"
                  >Email (Optional)</label
                >
                <InputText
                  id="study-contact-email"
                  v-model="correspondingEmail"
                  v-bind="correspondingEmailAttrs"
                  :invalid="!!errors.corresponding_author_email"
                  :disabled="correspondingAuthorIndex == null"
                  type="email"
                  fluid
                />
                <Message
                  v-if="errors.corresponding_author_email"
                  severity="error"
                  size="small"
                  variant="simple"
                >
                  {{ errors.corresponding_author_email }}
                </Message>
              </div>
              <div class="flex flex-col gap-2">
                <label for="study-contact-phone" class="font-medium text-sm"
                  >Phone number (Optional)</label
                >
                <InputText
                  id="study-contact-phone"
                  v-model="correspondingPhone"
                  v-bind="correspondingPhoneAttrs"
                  :disabled="correspondingAuthorIndex == null"
                  fluid
                />
              </div>
            </div>

            <Message v-if="submitError" severity="error" size="small">{{ submitError }}</Message>

            <div class="flex gap-2 mt-2">
              <Button
                type="submit"
                :label="editingId === null ? 'Add study' : 'Save changes'"
                :loading="submitting"
              />
              <Button label="Cancel" text type="button" @click="onCancel" />
            </div>
          </form>
        </TabPanel>
        <TabPanel v-if="editingId !== null" value="scenarios">
          <ScenariosList :study-id="editingId" />
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>
