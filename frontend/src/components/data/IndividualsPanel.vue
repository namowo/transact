<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import SkinDiseaseCategorySelect from '@/components/scenarios/SkinDiseaseCategorySelect.vue'
import DeterminationOfSheddingPropensityCategorySelect from '@/components/scenarios/DeterminationOfSheddingPropensityCategorySelect.vue'
import NamedCategoryRadioGroup from '@/components/scenarios/NamedCategoryRadioGroup.vue'
import { useConfirm } from '@/composables/useConfirm'
import { useStudyReadOnly } from '@/composables/useStudyAccess'
import { sexApi, dnaSheddingPropensityCategoryApi } from '@/api/categories'
import {
  createIndividual,
  deleteIndividual,
  listIndividuals,
  updateIndividual,
} from '@/api/individuals'
import { listContacts } from '@/api/contacts'
import ScenarioBadges from '@/components/data/ScenarioBadges.vue'
import ScenarioMultiSelect from '@/components/data/ScenarioMultiSelect.vue'
import type { Individual, Scenario } from '@/api/types'
import type { ContextMenuItem, TableColumn, TableRow } from '@nuxt/ui'
import { manualSorting, useTableView } from '@/composables/useTableView'
import { expandColumn, sortHeader } from '@/composables/tableColumns'
import TableFilterDrawer from '@/components/ui/TableFilterDrawer.vue'
import TablePagination from '@/components/ui/TablePagination.vue'
import TableLoadingSkeleton from '@/components/ui/TableLoadingSkeleton.vue'

const props = defineProps<{ studyId: string; scenarios: Scenario[]; scenarioId: string | null }>()

const readOnly = useStudyReadOnly()
const emit = defineEmits<{ 'update:count': [count: number] }>()

const confirm = useConfirm()

const sexIcons: Record<string, string> = {
  male: 'i-lucide-mars',
  female: 'i-lucide-venus',
  unknown: 'i-lucide-circle-help',
}

const sheddingPropensityIcons: Record<string, string> = {
  high: 'i-lucide-signal-high',
  intermediate: 'i-lucide-signal-medium',
  low: 'i-lucide-signal-low',
}

const individuals = ref<Individual[]>([])
const usedIndividualIds = ref<Set<string>>(new Set())
const loading = ref(false)
const loadError = ref('')

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const [loadedIndividuals, contacts] = await Promise.all([
      listIndividuals(props.studyId),
      listContacts(props.studyId),
    ])
    individuals.value = loadedIndividuals
    const used = new Set<string>()
    for (const contact of contacts) {
      if (contact.donor_surface?.individual_id) used.add(contact.donor_surface.individual_id)
      if (contact.recipient_surface?.individual_id)
        used.add(contact.recipient_surface.individual_id)
    }
    usedIndividualIds.value = used
  } catch {
    loadError.value = 'Could not load individuals. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

// With a scenario selected, only individuals used in that scenario show.
const visibleIndividuals = computed(() =>
  props.scenarioId === null
    ? individuals.value
    : individuals.value.filter((individual) =>
        individual.scenario_ids?.includes(props.scenarioId!),
      ),
)

watch(
  () => visibleIndividuals.value.length,
  (count) => emit('update:count', count),
  { immediate: true },
)

interface IndividualGroup {
  key: string
  sexId: string | null
  age: number | null
  dnaSheddingPropensityCategoryId: string | null
  skinDiseaseCategoryId: string | null
  determinationCategoryId: string | null
  members: Individual[]
  scenarioNames: string
}

function groupKey(individual: Individual): string {
  return [
    individual.sex_id,
    individual.age,
    individual.dna_shedding_propensity_category_id,
    individual.skin_disease_category_id,
    individual.determination_of_shedding_propensity_category_id,
  ]
    .map((value) => value ?? '')
    .join('::')
}

const individualGroups = computed<IndividualGroup[]>(() => {
  const groups = new Map<string, IndividualGroup>()
  for (const individual of visibleIndividuals.value) {
    const key = groupKey(individual)
    const existing = groups.get(key)
    if (existing) {
      existing.members.push(individual)
    } else {
      groups.set(key, {
        key,
        sexId: individual.sex_id ?? null,
        age: individual.age ?? null,
        dnaSheddingPropensityCategoryId: individual.dna_shedding_propensity_category_id ?? null,
        skinDiseaseCategoryId: individual.skin_disease_category_id ?? null,
        determinationCategoryId:
          individual.determination_of_shedding_propensity_category_id ?? null,
        members: [individual],
        scenarioNames: '',
      })
    }
  }
  return [...groups.values()].map((group) => ({
    ...group,
    scenarioNames: groupScenarioNames(group).join(', '),
  }))
})

function scenarioNames(ids: string[]): string[] {
  return props.scenarios.filter((s) => ids.includes(s.id)).map((s) => s.name)
}

function groupScenarioNames(group: IndividualGroup): string[] {
  return scenarioNames([...new Set(group.members.flatMap((member) => member.scenario_ids ?? []))])
}

function usedMembers(group: IndividualGroup): Individual[] {
  return group.members.filter((member) => usedIndividualIds.value.has(member.id))
}

function memberLabel(member: Individual, group: IndividualGroup): string {
  if (member.name) return member.name
  const position = group.members.indexOf(member) + 1
  return `Individual ${position}`
}

const sexName = (group: IndividualGroup) => group.members[0]?.sex?.name
const sheddingName = (group: IndividualGroup) =>
  group.members[0]?.dna_shedding_propensity_category?.name

const view = useTableView(individualGroups, {
  searchFields: [sexName, 'age', sheddingName, 'scenarioNames'],
  filters: {
    sex: { field: sexName },
    age: { field: 'age' },
    shedding: { field: sheddingName },
    scenario: { field: 'scenarioNames' },
  },
  sortAccessors: { sex: sexName, shedding: sheddingName },
})

const columns = computed<TableColumn<IndividualGroup>[]>(() => [
  expandColumn(),
  { id: 'index', header: '#', meta: { class: { td: 'w-12' } } },
  { id: 'count', header: 'Count', meta: { class: { td: 'w-20' } } },
  { id: 'sex', header: sortHeader('Sex') },
  { id: 'age', accessorKey: 'age', header: sortHeader('Age') },
  { id: 'shedding', header: sortHeader('DNA shedding propensity') },
  { id: 'scenarioNames', accessorKey: 'scenarioNames', header: sortHeader('Scenario') },
  ...(readOnly.value ? [] : [{ id: 'actions', header: '', meta: { class: { td: 'w-24' } } }]),
])

const memberColumns = computed<TableColumn<Individual>[]>(() => [
  { id: 'name', accessorKey: 'name', header: 'Name' },
  { id: 'sex', header: 'Sex' },
  { id: 'age', accessorKey: 'age', header: 'Age' },
  { id: 'shedding', header: 'DNA shedding propensity' },
  ...(readOnly.value ? [] : [{ id: 'actions', header: '', meta: { class: { td: 'w-12' } } }]),
])

interface IndividualFormState {
  count: number | null
  sexId: string | null
  age: number | null
  dnaSheddingPropensityCategoryId: string | null
  skinDiseaseCategoryId: string | null
  determinationCategoryId: string | null
}

function emptyIndividualForm(group: IndividualGroup | null): IndividualFormState {
  return {
    count: group?.members.length ?? 1,
    sexId: group?.sexId ?? null,
    age: group?.age ?? null,
    dnaSheddingPropensityCategoryId: group?.dnaSheddingPropensityCategoryId ?? null,
    skinDiseaseCategoryId: group?.skinDiseaseCategoryId ?? null,
    determinationCategoryId: group?.determinationCategoryId ?? null,
  }
}

const individualSchema = yup.object({
  count: yup
    .number()
    .required('Enter how many individuals this group should have.')
    .integer('Enter a whole number.')
    .min(1, 'Enter at least 1.')
    .max(500, 'Enter at most 500.'),
  sexId: yup.string().nullable().defined(),
  age: yup.number().nullable().min(0, 'Age must be zero or greater.'),
  dnaSheddingPropensityCategoryId: yup.string().nullable().defined(),
  skinDiseaseCategoryId: yup.string().nullable().defined(),
  determinationCategoryId: yup.string().nullable().defined(),
})

const {
  defineField: defineIndividualField,
  errors: individualErrors,
  handleSubmit: handleIndividualSubmit,
  resetForm: resetIndividualForm,
} = useForm<IndividualFormState>({
  validationSchema: individualSchema,
  initialValues: emptyIndividualForm(null),
})

const [individualCount] = defineIndividualField('count')
const [individualSexId] = defineIndividualField('sexId')
const [individualAge] = defineIndividualField('age')
const [individualDnaSheddingPropensityCategoryId] = defineIndividualField(
  'dnaSheddingPropensityCategoryId',
)
const [individualSkinDiseaseCategoryId] = defineIndividualField('skinDiseaseCategoryId')
const [individualDeterminationCategoryId] = defineIndividualField('determinationCategoryId')

const individualDialogVisible = ref(false)
const editingGroup = ref<IndividualGroup | null>(null)
const savingIndividual = ref(false)
const individualSaveError = ref('')
const savingIndividualProgress = ref({ done: 0, total: 0 })

const editScenarioIds = ref<string[]>([])
const editScenarioError = ref('')
const scenarioRequiredMessage = 'Select at least one scenario.'

function openEditGroupDialog(group: IndividualGroup) {
  editingGroup.value = group
  editScenarioIds.value = [...new Set(group.members.flatMap((member) => member.scenario_ids ?? []))]
  editScenarioError.value = ''
  resetIndividualForm({ values: emptyIndividualForm(group) })
  individualSaveError.value = ''
  individualDialogVisible.value = true
}

function confirmAndSaveIndividualForm(values: IndividualFormState) {
  const group = editingGroup.value
  if (group === null) return
  const targetCount = values.count ?? group.members.length
  const removedCount = group.members.length - targetCount
  if (removedCount <= 0) {
    void applyIndividualFormSave(values)
    return
  }
  const toRemove = pickMembersToRemove(group.members, removedCount)
  const usedToRemove = toRemove.filter((member) => usedIndividualIds.value.has(member.id))
  if (usedToRemove.length === 0) {
    void applyIndividualFormSave(values)
    return
  }
  confirm.require({
    header: 'Individuals in use',
    message: `Reducing the count will delete ${usedToRemove.length} individual(s) already used in a recorded contact. Those contacts will lose their individual. Continue?`,
    acceptLabel: 'Delete anyway',
    acceptColor: 'error',
    rejectLabel: 'Cancel',
    accept: () => void applyIndividualFormSave(values),
  })
}

// Prefer removing members not yet referenced by a recorded contact.
function pickMembersToRemove(members: Individual[], count: number): Individual[] {
  const unused = members.filter((member) => !usedIndividualIds.value.has(member.id))
  const used = members.filter((member) => usedIndividualIds.value.has(member.id))
  return [...unused, ...used].slice(0, count)
}

async function applyIndividualFormSave(values: IndividualFormState) {
  if (editingGroup.value === null) return
  savingIndividual.value = true
  individualSaveError.value = ''
  const payload = {
    sex_id: values.sexId,
    age: values.age,
    dna_shedding_propensity_category_id: values.dnaSheddingPropensityCategoryId,
    skin_disease_category_id: values.skinDiseaseCategoryId,
    determination_of_shedding_propensity_category_id: values.determinationCategoryId,
    scenario_ids: editScenarioIds.value,
  }
  try {
    const members = editingGroup.value.members
    const targetCount = values.count ?? members.length
    const toRemove =
      targetCount < members.length ? pickMembersToRemove(members, members.length - targetCount) : []
    const removeIds = new Set(toRemove.map((member) => member.id))
    const remainingMembers = members.filter((member) => !removeIds.has(member.id))
    const toCreate = Math.max(targetCount - remainingMembers.length, 0)

    const totalSteps = remainingMembers.length + toRemove.length + toCreate
    savingIndividualProgress.value = { done: 0, total: totalSteps }

    const updated: Individual[] = []
    for (const member of remainingMembers) {
      updated.push(await updateIndividual(member.id, payload))
      savingIndividualProgress.value.done += 1
    }
    for (const member of toRemove) {
      await deleteIndividual(member.id)
      savingIndividualProgress.value.done += 1
    }
    const created: Individual[] = []
    for (let i = 0; i < toCreate; i++) {
      created.push(await createIndividual({ ...payload, study_id: props.studyId }))
      savingIndividualProgress.value.done += 1
    }

    const updatedById = new Map(updated.map((individual) => [individual.id, individual]))
    individuals.value = [
      ...individuals.value
        .filter((candidate) => !removeIds.has(candidate.id))
        .map((candidate) => updatedById.get(candidate.id) ?? candidate),
      ...created,
    ]
    if (toRemove.length > 0) {
      usedIndividualIds.value = new Set(
        [...usedIndividualIds.value].filter((id) => !removeIds.has(id)),
      )
    }
    individualDialogVisible.value = false
  } catch {
    individualSaveError.value = `Could not update all individuals in this group. ${savingIndividualProgress.value.done} of ${savingIndividualProgress.value.total} were processed before the error.`
  } finally {
    savingIndividual.value = false
  }
}

const submitIndividualForm = handleIndividualSubmit((values) => {
  if (editScenarioError.value) return
  confirmAndSaveIndividualForm(values)
})

function saveIndividualForm() {
  editScenarioError.value = editScenarioIds.value.length ? '' : scenarioRequiredMessage
  void submitIndividualForm()
}

watch(editScenarioIds, (ids) => {
  if (ids.length) editScenarioError.value = ''
})

// -- Add individuals dialog (one or many, sharing the same details) --

interface BatchFormState {
  count: number | null
  sexId: string | null
  age: number | null
  dnaSheddingPropensityCategoryId: string | null
  skinDiseaseCategoryId: string | null
  determinationCategoryId: string | null
}

function emptyBatchForm(): BatchFormState {
  return {
    count: 1,
    sexId: null,
    age: null,
    dnaSheddingPropensityCategoryId: null,
    skinDiseaseCategoryId: null,
    determinationCategoryId: null,
  }
}

const batchSchema = yup.object({
  count: yup
    .number()
    .required('Enter how many individuals to add.')
    .integer('Enter a whole number.')
    .min(1, 'Enter at least 1.')
    .max(500, 'Add at most 500 at a time.'),
  sexId: yup.string().nullable().defined(),
  age: yup.number().nullable().min(0, 'Age must be zero or greater.'),
  dnaSheddingPropensityCategoryId: yup.string().nullable().defined(),
  skinDiseaseCategoryId: yup.string().nullable().defined(),
  determinationCategoryId: yup.string().nullable().defined(),
})

const {
  defineField: defineBatchField,
  errors: batchErrors,
  handleSubmit: handleBatchSubmit,
  resetForm: resetBatchForm,
} = useForm<BatchFormState>({
  validationSchema: batchSchema,
  initialValues: emptyBatchForm(),
})

const [batchCount] = defineBatchField('count')
const [batchSexId] = defineBatchField('sexId')
const [batchAge] = defineBatchField('age')
const [batchDnaSheddingPropensityCategoryId] = defineBatchField('dnaSheddingPropensityCategoryId')
const [batchSkinDiseaseCategoryId] = defineBatchField('skinDiseaseCategoryId')
const [batchDeterminationCategoryId] = defineBatchField('determinationCategoryId')

const batchDialogVisible = ref(false)
const savingBatch = ref(false)
const batchSaveError = ref('')
const batchProgress = ref({ done: 0, total: 0 })

const batchScenarioIds = ref<string[]>([])
const batchScenarioError = ref('')

watch(batchScenarioIds, (ids) => {
  if (ids.length) batchScenarioError.value = ''
})

function openBatchDialog() {
  batchScenarioIds.value = props.scenarioId ? [props.scenarioId] : []
  batchScenarioError.value = ''
  resetBatchForm({ values: emptyBatchForm() })
  batchSaveError.value = ''
  batchDialogVisible.value = true
}

function saveBatchForm() {
  batchScenarioError.value = batchScenarioIds.value.length ? '' : scenarioRequiredMessage
  void submitBatchForm()
}

const submitBatchForm = handleBatchSubmit(async (values) => {
  if (batchScenarioError.value) return
  savingBatch.value = true
  batchSaveError.value = ''
  const total = values.count ?? 0
  batchProgress.value = { done: 0, total }
  const payload = {
    sex_id: values.sexId,
    age: values.age,
    dna_shedding_propensity_category_id: values.dnaSheddingPropensityCategoryId,
    skin_disease_category_id: values.skinDiseaseCategoryId,
    determination_of_shedding_propensity_category_id: values.determinationCategoryId,
    scenario_ids: batchScenarioIds.value,
  }
  try {
    const created: Individual[] = []
    for (let i = 0; i < total; i++) {
      created.push(await createIndividual({ ...payload, study_id: props.studyId }))
      batchProgress.value = { done: i + 1, total }
    }
    individuals.value = [...individuals.value, ...created]
    batchDialogVisible.value = false
  } catch {
    batchSaveError.value = `Could not add all individuals. ${batchProgress.value.done} of ${total} were added before the error.`
  } finally {
    savingBatch.value = false
  }
})

// -- Delete a whole group --

const deletingGroup = ref(false)

function confirmDeleteGroup(group: IndividualGroup) {
  const used = usedMembers(group)
  const label = group.members.length > 1 ? `${group.members.length} individuals` : 'this individual'
  const usedWarning =
    used.length > 0
      ? ` ${used.length} of them ${used.length > 1 ? 'are' : 'is'} already used in a recorded contact, which will lose its individual.`
      : ''
  confirm.require({
    header: 'Delete individuals',
    message: `Delete ${label}? This cannot be undone.${usedWarning}`,
    acceptLabel: 'Delete',
    acceptColor: 'error',
    rejectLabel: 'Cancel',
    accept: () => void deleteGroup(group),
  })
}

async function deleteGroup(group: IndividualGroup) {
  deletingGroup.value = true
  try {
    for (const member of group.members) {
      await deleteIndividual(member.id)
    }
    const removeIds = new Set(group.members.map((member) => member.id))
    individuals.value = individuals.value.filter((candidate) => !removeIds.has(candidate.id))
    usedIndividualIds.value = new Set(
      [...usedIndividualIds.value].filter((id) => !removeIds.has(id)),
    )
  } finally {
    deletingGroup.value = false
  }
}

// -- Context menu --

function menuItems(group: IndividualGroup): ContextMenuItem[] {
  return [
    {
      label: 'Edit',
      icon: 'i-lucide-pencil',
      onSelect: () => openEditGroupDialog(group),
    },
    {
      label: 'Delete',
      icon: 'i-lucide-trash-2',
      color: 'error',
      onSelect: () => confirmDeleteGroup(group),
    },
  ]
}

// The right-clicked row's menu.
const contextMenuItems = ref<ContextMenuItem[]>([])

function onRowContextMenu(_event: Event, row: TableRow<IndividualGroup>) {
  contextMenuItems.value = readOnly.value ? [] : menuItems(row.original)
}

// -- Expansion + inline editing of individual members --

const expandedGroupRows = ref<Record<string, boolean>>({})
const sexOptions = ref<{ id: string; name?: string | null }[]>([])
const sheddingPropensityOptions = ref<{ id: string; name?: string | null }[]>([])

async function loadInlineEditOptions() {
  const [sexes, sheddingPropensities] = await Promise.all([
    sexApi.list(),
    dnaSheddingPropensityCategoryApi.list(),
  ])
  sexOptions.value = sexes
  sheddingPropensityOptions.value = sheddingPropensities
}

const editMode = ref(false)

function toggleEditMode() {
  editMode.value = !editMode.value
  if (editMode.value) {
    void loadInlineEditOptions()
    // Expand every group so a member that moves into a different group
    // after an inline edit (e.g. its age changes) stays visible and
    // editable instead of silently collapsing into a hidden row.
    const expanded: Record<string, boolean> = {}
    for (const group of individualGroups.value) expanded[group.key] = true
    expandedGroupRows.value = expanded
  }
}

// Keep every group expanded while in edit mode, even as inline edits
// re-shuffle members into newly created/split groups with keys that
// weren't expanded yet.
watch(individualGroups, (groups) => {
  if (!editMode.value) return
  const expanded = { ...expandedGroupRows.value }
  for (const group of groups) expanded[group.key] = true
  expandedGroupRows.value = expanded
})

const savingMemberIds = ref<Set<string>>(new Set())

async function saveMemberField(member: Individual, patch: Partial<Individual>) {
  const next = new Set(savingMemberIds.value)
  next.add(member.id)
  savingMemberIds.value = next
  try {
    const updated = await updateIndividual(member.id, {
      name: patch.name !== undefined ? patch.name : member.name,
      sex_id: patch.sex_id !== undefined ? patch.sex_id : member.sex_id,
      age: patch.age !== undefined ? patch.age : member.age,
      skin_disease_category_id:
        patch.skin_disease_category_id !== undefined
          ? patch.skin_disease_category_id
          : member.skin_disease_category_id,
      dna_shedding_propensity_category_id:
        patch.dna_shedding_propensity_category_id !== undefined
          ? patch.dna_shedding_propensity_category_id
          : member.dna_shedding_propensity_category_id,
      determination_of_shedding_propensity_category_id:
        member.determination_of_shedding_propensity_category_id,
    })
    individuals.value = individuals.value.map((candidate) =>
      candidate.id === updated.id ? updated : candidate,
    )
  } finally {
    const after = new Set(savingMemberIds.value)
    after.delete(member.id)
    savingMemberIds.value = after
  }
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <UAlert v-if="loadError" color="error" variant="outline" :description="loadError" />

    <div class="flex items-center justify-between">
      <h4 class="font-medium">Individuals</h4>
      <UButton
        v-if="!readOnly"
        data-tour="add-individuals"
        label="Add individuals"
        icon="i-lucide-plus"
        variant="outline"
        @click="openBatchDialog"
      />
    </div>
    <div class="flex flex-col gap-3">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <UInput
          v-model="view.search"
          icon="i-lucide-search"
          placeholder="Keyword Search"
          class="w-full max-w-sm"
        />
        <div class="flex items-center gap-2">
          <UButton
            v-if="!readOnly"
            type="button"
            :label="editMode ? 'Done editing' : 'Edit table'"
            :icon="editMode ? 'i-lucide-check' : 'i-lucide-pencil-line'"
            :variant="editMode ? 'solid' : 'outline'"
            @click="toggleEditMode()"
          />
          <TableFilterDrawer :active-count="view.activeFilterCount" @reset="view.resetFilters()">
            <UFormField label="Sex">
              <UInput v-model="view.filters.sex" placeholder="Search by sex" class="w-full" />
            </UFormField>
            <UFormField label="Age">
              <UInput v-model="view.filters.age" placeholder="Search by age" class="w-full" />
            </UFormField>
            <UFormField label="DNA shedding propensity">
              <UInput
                v-model="view.filters.shedding"
                placeholder="Search by shedding propensity"
                class="w-full"
              />
            </UFormField>
            <UFormField label="Scenario">
              <UInput
                v-model="view.filters.scenario"
                placeholder="Search by scenario"
                class="w-full"
              />
            </UFormField>
          </TableFilterDrawer>
        </div>
      </div>

      <UContextMenu :items="contextMenuItems" :disabled="readOnly">
        <UTable
          v-model:expanded="expandedGroupRows"
          v-model:sorting="view.sorting"
          :sorting-options="manualSorting"
          :data="view.rows"
          :columns="columns"
          :loading="loading || deletingGroup"
          :get-row-id="(group: IndividualGroup) => group.key"
          :on-contextmenu="onRowContextMenu"
        >
          <template #loading>
            <TableLoadingSkeleton />
          </template>

          <template #index-cell="{ row }">{{ row.index + 1 }}</template>
          <template #count-cell="{ row: { original: data } }">
            <UBadge v-if="data.members.length > 1" color="neutral" variant="subtle">
              {{ data.members.length }}x
            </UBadge>
          </template>
          <template #sex-cell="{ row: { original: data } }">
            <UBadge v-if="data.members[0].sex?.name" color="neutral" variant="outline">
              {{ data.members[0].sex.name }}
            </UBadge>
            <span v-else>—</span>
          </template>
          <template #age-cell="{ row }">{{ row.original.age ?? '—' }}</template>
          <template #shedding-cell="{ row: { original: data } }">
            <UBadge
              v-if="data.members[0].dna_shedding_propensity_category?.name"
              color="neutral"
              variant="outline"
            >
              {{ data.members[0].dna_shedding_propensity_category.name }}
            </UBadge>
            <span v-else>—</span>
          </template>
          <template #scenarioNames-cell="{ row }"
            ><ScenarioBadges :names="groupScenarioNames(row.original)"
          /></template>
          <template #actions-cell="{ row: { original: data } }">
            <span class="flex items-center justify-end gap-1">
              <UButton
                icon="i-lucide-pencil"
                color="neutral"
                variant="ghost"
                square
                aria-label="Edit group"
                @click="openEditGroupDialog(data)"
              />
              <UDropdownMenu :items="menuItems(data)" :content="{ align: 'end' }">
                <UButton
                  icon="i-lucide-more-vertical"
                  color="neutral"
                  variant="ghost"
                  square
                  aria-label="Individual options"
                />
              </UDropdownMenu>
            </span>
          </template>

          <template #expanded="{ row: { original: group } }">
            <div class="flex flex-col gap-2 py-2">
              <div class="px-2">
                <p class="text-sm text-surface-500 dark:text-surface-400">
                  {{
                    group.members.length > 1
                      ? `${group.members.length} individuals in this group`
                      : '1 individual'
                  }}
                </p>
              </div>
              <UTable
                :data="group.members"
                :columns="memberColumns"
                :get-row-id="(m: Individual) => m.id"
              >
                <template #name-cell="{ row: { original: member } }">
                  <UInput
                    v-if="editMode"
                    :model-value="member.name ?? ''"
                    placeholder="Unnamed"
                    size="sm"
                    :loading="savingMemberIds.has(member.id)"
                    @change="
                      (e: Event) =>
                        saveMemberField(member, {
                          name: (e.target as HTMLInputElement).value || null,
                        })
                    "
                  />
                  <span v-else class="flex items-center gap-1.5">
                    <UIcon name="i-lucide-user" class="shrink-0" />
                    {{ memberLabel(member, group) }}
                  </span>
                </template>
                <template #sex-cell="{ row: { original: member } }">
                  <USelectMenu
                    v-if="editMode"
                    :model-value="member.sex_id ?? undefined"
                    :items="sexOptions.map((s) => ({ label: s.name, value: s.id }))"
                    value-key="value"
                    :search-input="false"
                    clear
                    placeholder="—"
                    size="sm"
                    :loading="savingMemberIds.has(member.id)"
                    @update:model-value="
                      (value: string) => saveMemberField(member, { sex_id: value ?? null })
                    "
                  />
                  <template v-else>
                    <UBadge v-if="member.sex?.name" color="neutral" variant="outline">
                      {{ member.sex.name }}
                    </UBadge>
                    <span v-else>—</span>
                  </template>
                </template>
                <template #age-cell="{ row: { original: member } }">
                  <UInputNumber
                    v-if="editMode"
                    :model-value="member.age ?? undefined"
                    :min="0"
                    size="sm"
                    class="w-24"
                    :loading="savingMemberIds.has(member.id)"
                    @update:model-value="
                      (value: number) => saveMemberField(member, { age: value ?? null })
                    "
                  />
                  <span v-else>{{ member.age ?? '—' }}</span>
                </template>
                <template #shedding-cell="{ row: { original: member } }">
                  <USelectMenu
                    v-if="editMode"
                    :model-value="member.dna_shedding_propensity_category_id ?? undefined"
                    :items="sheddingPropensityOptions.map((c) => ({ label: c.name, value: c.id }))"
                    value-key="value"
                    :search-input="false"
                    clear
                    placeholder="—"
                    size="sm"
                    :loading="savingMemberIds.has(member.id)"
                    @update:model-value="
                      (value: string) =>
                        saveMemberField(member, {
                          dna_shedding_propensity_category_id: value ?? null,
                        })
                    "
                  />
                  <template v-else>
                    <UBadge
                      v-if="member.dna_shedding_propensity_category?.name"
                      color="neutral"
                      variant="outline"
                    >
                      {{ member.dna_shedding_propensity_category.name }}
                    </UBadge>
                    <span v-else>—</span>
                  </template>
                </template>
                <template #actions-cell="{ row: { original: member } }">
                  <UButton
                    icon="i-lucide-trash-2"
                    color="neutral"
                    variant="ghost"
                    square
                    aria-label="Delete individual"
                    @click="
                      confirmDeleteGroup({
                        key: member.id,
                        sexId: member.sex_id ?? null,
                        age: member.age ?? null,
                        dnaSheddingPropensityCategoryId:
                          member.dna_shedding_propensity_category_id ?? null,
                        skinDiseaseCategoryId: member.skin_disease_category_id ?? null,
                        determinationCategoryId:
                          member.determination_of_shedding_propensity_category_id ?? null,
                        members: [member],
                        scenarioNames: '',
                      })
                    "
                  />
                </template>
              </UTable>
            </div>
          </template>
        </UTable>
      </UContextMenu>
      <TablePagination
        v-model:page="view.page"
        v-model:page-size="view.pageSize"
        :total="view.total"
      />
    </div>

    <UModal
      v-model:open="individualDialogVisible"
      :title="
        editingGroup && editingGroup.members.length > 1
          ? `Edit ${editingGroup.members.length} individuals`
          : 'Edit individual'
      "
      :ui="{ content: 'max-w-md', footer: 'justify-end' }"
    >
      <template #body>
        <div class="flex flex-col gap-4">
          <p
            v-if="editingGroup && editingGroup.members.length > 1"
            class="text-sm text-surface-500 dark:text-surface-400"
          >
            These individuals currently share the same details. Changes here apply to all
            {{ editingGroup.members.length }} of them.
          </p>
          <ScenarioMultiSelect
            v-model="editScenarioIds"
            :scenarios="scenarios"
            required
            :error="editScenarioError"
          />
          <UFormField label="Count" :error="individualErrors.count">
            <UInputNumber v-model="individualCount" :min="1" :max="500" class="w-full" />
          </UFormField>
          <p
            v-if="editingGroup && usedMembers(editingGroup).length > 0"
            class="text-sm text-warning"
          >
            {{ usedMembers(editingGroup).length }} of these individuals
            {{ usedMembers(editingGroup).length > 1 ? 'are' : 'is' }} already used in a recorded
            contact. Lowering the count below that may remove one of them.
          </p>
          <NamedCategoryRadioGroup
            v-model="individualSexId"
            label="Sex"
            hint="Optional"
            :api="sexApi"
            :icons="sexIcons"
          />
          <UFormField label="Age" hint="Optional" :error="individualErrors.age">
            <UInputNumber v-model="individualAge" orientation="vertical" class="w-full" />
          </UFormField>
          <NamedCategoryRadioGroup
            v-model="individualDnaSheddingPropensityCategoryId"
            label="DNA shedding propensity"
            hint="Optional"
            :api="dnaSheddingPropensityCategoryApi"
            :icons="sheddingPropensityIcons"
            none-label="Not determined"
          />
          <SkinDiseaseCategorySelect v-model="individualSkinDiseaseCategoryId" />
          <DeterminationOfSheddingPropensityCategorySelect
            v-model="individualDeterminationCategoryId"
          />
          <UProgress
            v-if="savingIndividual && savingIndividualProgress.total > 1"
            :model-value="savingIndividualProgress.done"
            :max="savingIndividualProgress.total"
          />
          <UAlert
            v-if="individualSaveError"
            color="error"
            variant="outline"
            :description="individualSaveError"
          />
        </div>
      </template>
      <template #footer>
        <UButton
          label="Cancel"
          icon="i-lucide-x"
          variant="ghost"
          @click="individualDialogVisible = false"
        />
        <UButton
          label="Save"
          icon="i-lucide-save"
          :loading="savingIndividual"
          @click="saveIndividualForm"
        />
      </template>
    </UModal>

    <UModal
      v-model:open="batchDialogVisible"
      title="Add individuals"
      :ui="{ content: 'max-w-md', footer: 'justify-end' }"
    >
      <template #body>
        <div class="flex flex-col gap-4" data-tour="individuals-dialog">
          <p class="text-sm text-surface-500 dark:text-surface-400">
            Leave the count at 1 to add a single individual, or raise it to add several at once
            sharing the same details below. They'll show up as a single grouped row until you change
            one of them.
          </p>
          <ScenarioMultiSelect
            v-model="batchScenarioIds"
            :scenarios="scenarios"
            required
            :error="batchScenarioError"
          />
          <UFormField label="Number of individuals" :error="batchErrors.count">
            <UInputNumber v-model="batchCount" :min="1" :max="500" class="w-full" />
          </UFormField>
          <NamedCategoryRadioGroup
            v-model="batchSexId"
            label="Sex"
            hint="Optional"
            :api="sexApi"
            :icons="sexIcons"
          />
          <UFormField label="Age" hint="Optional" :error="batchErrors.age">
            <UInputNumber v-model="batchAge" orientation="vertical" class="w-full" />
          </UFormField>
          <NamedCategoryRadioGroup
            v-model="batchDnaSheddingPropensityCategoryId"
            label="DNA shedding propensity"
            hint="Optional"
            :api="dnaSheddingPropensityCategoryApi"
            :icons="sheddingPropensityIcons"
            none-label="Not determined"
          />
          <SkinDiseaseCategorySelect v-model="batchSkinDiseaseCategoryId" />
          <DeterminationOfSheddingPropensityCategorySelect v-model="batchDeterminationCategoryId" />
          <UProgress
            v-if="savingBatch"
            :model-value="batchProgress.done"
            :max="batchProgress.total"
          />
          <UAlert
            v-if="batchSaveError"
            color="error"
            variant="outline"
            :description="batchSaveError"
          />
        </div>
      </template>
      <template #footer>
        <UButton
          label="Cancel"
          icon="i-lucide-x"
          variant="ghost"
          @click="batchDialogVisible = false"
        />
        <UButton
          label="Add individuals"
          icon="i-lucide-plus"
          :loading="savingBatch"
          @click="saveBatchForm"
        />
      </template>
    </UModal>
  </div>
</template>
