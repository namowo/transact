<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import ContextMenu from 'openvue/contextmenu'
import { FilterMatchMode } from '@openvue/core/api'
import DataTableSkeleton from '@/components/data/DataTableSkeleton.vue'
import SkinDiseaseCategorySelect from '@/components/scenarios/SkinDiseaseCategorySelect.vue'
import DeterminationOfSheddingPropensityCategorySelect from '@/components/scenarios/DeterminationOfSheddingPropensityCategorySelect.vue'
import NamedCategoryRadioGroup from '@/components/scenarios/NamedCategoryRadioGroup.vue'
import { useConfirm } from '@/composables/useConfirm'
import { sexApi, dnaSheddingPropensityCategoryApi } from '@/api/categories'
import {
  createIndividual,
  deleteIndividual,
  listIndividuals,
  updateIndividual,
} from '@/api/individuals'
import { listContacts } from '@/api/contacts'
import type { Individual } from '@/api/types'
import type { MenuItem } from 'openvue/menuitem'

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
    const [loadedIndividuals, contacts] = await Promise.all([listIndividuals(), listContacts()])
    individuals.value = loadedIndividuals
    const used = new Set<string>()
    for (const contact of contacts) {
      if (contact.donor_surface?.individual_id) used.add(contact.donor_surface.individual_id)
      if (contact.recipient_surface?.individual_id) used.add(contact.recipient_surface.individual_id)
    }
    usedIndividualIds.value = used
  } catch {
    loadError.value = 'Could not load individuals. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

interface IndividualGroup {
  key: string
  sexId: string | null
  age: number | null
  dnaSheddingPropensityCategoryId: string | null
  skinDiseaseCategoryId: string | null
  determinationCategoryId: string | null
  members: Individual[]
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
  for (const individual of individuals.value) {
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
        determinationCategoryId: individual.determination_of_shedding_propensity_category_id ?? null,
        members: [individual],
      })
    }
  }
  return [...groups.values()]
})

function usedMembers(group: IndividualGroup): Individual[] {
  return group.members.filter((member) => usedIndividualIds.value.has(member.id))
}

function initIndividualFilters() {
  return {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
    'sex.name': { value: null, matchMode: FilterMatchMode.CONTAINS },
    age: { value: null, matchMode: FilterMatchMode.CONTAINS },
    'skin_disease_category.name': { value: null, matchMode: FilterMatchMode.CONTAINS },
  }
}

const individualFilters = ref(initIndividualFilters())

function clearIndividualFilters() {
  individualFilters.value = initIndividualFilters()
}

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

function openEditGroupDialog(group: IndividualGroup) {
  editingGroup.value = group
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
  }
  try {
    const members = editingGroup.value.members
    const targetCount = values.count ?? members.length
    const toRemove = targetCount < members.length ? pickMembersToRemove(members, members.length - targetCount) : []
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
      created.push(await createIndividual(payload))
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

const saveIndividualForm = handleIndividualSubmit((values) => confirmAndSaveIndividualForm(values))

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

function openBatchDialog() {
  resetBatchForm({ values: emptyBatchForm() })
  batchSaveError.value = ''
  batchDialogVisible.value = true
}

const saveBatchForm = handleBatchSubmit(async (values) => {
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
  }
  try {
    const created: Individual[] = []
    for (let i = 0; i < total; i++) {
      created.push(await createIndividual(payload))
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

const contextMenu = ref<InstanceType<typeof ContextMenu>>()
const selectedGroup = ref<IndividualGroup>()

const contextMenuItems = computed<MenuItem[]>(() => {
  const group = selectedGroup.value
  if (!group) return []
  return [
    {
      label: 'Edit',
      icon: 'i-lucide-pencil',
      command: () => openEditGroupDialog(group),
    },
    {
      label: 'Delete',
      icon: 'i-lucide-trash-2',
      command: () => confirmDeleteGroup(group),
    },
  ]
})

function onRowContextMenu(event: { originalEvent: Event; data: IndividualGroup }) {
  selectedGroup.value = event.data
  contextMenu.value?.show(event.originalEvent)
}

function openRowContextMenu(event: Event, group: IndividualGroup) {
  selectedGroup.value = group
  contextMenu.value?.show(event)
}

function onRowClick(event: { data: IndividualGroup }) {
  openEditGroupDialog(event.data)
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <UAlert v-if="loadError" color="error" variant="outline" :description="loadError" />

    <div class="flex items-center justify-between">
      <h4 class="font-medium">Individuals</h4>
      <UButton
        label="Add individuals"
        icon="i-lucide-plus"
        variant="outline"
        @click="openBatchDialog"
      />
    </div>
    <div class="overflow-x-auto">
      <div class="mb-3 flex items-center justify-between gap-3">
        <UButton
          type="button"
          icon="i-lucide-filter-x"
          variant="outline"
          size="sm"
          @click="clearIndividualFilters()"
        >
          Clear Filters
        </UButton>
        <UInput
          v-model="individualFilters['global'].value"
          type="text"
          icon="i-lucide-search"
          placeholder="Keyword Search"
        />
      </div>

      <ContextMenu ref="contextMenu" :model="contextMenuItems" />

      <DataTableSkeleton v-if="loading" :columns="4" />
      <DataTable
        v-else
        v-model:filters="individualFilters"
        v-model:context-menu-selection="selectedGroup"
        :value="individualGroups"
        :loading="deletingGroup"
        data-key="key"
        filterDisplay="menu"
        context-menu
        :globalFilterFields="['sex.name', 'age', 'skin_disease_category.name']"
        :row-class="() => 'cursor-pointer hover:bg-elevated'"
        @row-contextmenu="onRowContextMenu"
        @row-click="onRowClick"
      >
        <Column header="#" style="width: 3rem">
          <template #body="{ index }">{{ index + 1 }}</template>
        </Column>
        <Column header="Count" style="width: 5rem">
          <template #body="{ data }">
            <UBadge v-if="data.members.length > 1" color="neutral" variant="subtle">
              {{ data.members.length }}x
            </UBadge>
          </template>
        </Column>
        <Column
          field="sex.name"
          header="Sex"
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #body="{ data }">
            <UBadge v-if="data.members[0].sex?.name" color="neutral" variant="outline">
              {{ data.members[0].sex.name }}
            </UBadge>
            <span v-else>—</span>
          </template>
          <template #filter="{ filterModel }">
            <UInput v-model="filterModel.value" type="text" placeholder="Search by sex" />
          </template>
        </Column>
        <Column
          field="age"
          header="Age"
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #body="{ data }">{{ data.age ?? '—' }}</template>
          <template #filter="{ filterModel }">
            <UInput v-model="filterModel.value" type="text" placeholder="Search by age" />
          </template>
        </Column>
        <Column
          field="skin_disease_category.name"
          header="Skin disease"
          sortable
          :showFilterOperator="false"
          :showAddButton="false"
        >
          <template #body="{ data }">
            <UBadge v-if="data.members[0].skin_disease_category?.name" color="neutral" variant="outline">
              {{ data.members[0].skin_disease_category.name }}
            </UBadge>
            <span v-else>—</span>
          </template>
          <template #filter="{ filterModel }">
            <UInput v-model="filterModel.value" type="text" placeholder="Search by skin disease" />
          </template>
        </Column>
        <Column header="" style="width: 4rem">
          <template #body="{ data }">
            <UButton
              icon="i-lucide-more-vertical"
              color="neutral"
              variant="ghost"
              square
              aria-label="Individual options"
              @click.stop="openRowContextMenu($event, data)"
            />
          </template>
        </Column>
      </DataTable>
    </div>

    <UModal
      v-model:open="individualDialogVisible"
      :title="editingGroup && editingGroup.members.length > 1 ? `Edit ${editingGroup.members.length} individuals` : 'Edit individual'"
      :ui="{ content: 'max-w-md', footer: 'justify-end' }"
    >
      <template #body>
        <div class="flex flex-col gap-4">
          <p v-if="editingGroup && editingGroup.members.length > 1" class="text-sm text-surface-500 dark:text-surface-400">
            These individuals currently share the same details. Changes here apply to all
            {{ editingGroup.members.length }} of them.
          </p>
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
        <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="individualDialogVisible = false" />
        <UButton label="Save" icon="i-lucide-save" :loading="savingIndividual" @click="saveIndividualForm" />
      </template>
    </UModal>

    <UModal
      v-model:open="batchDialogVisible"
      title="Add individuals"
      :ui="{ content: 'max-w-md', footer: 'justify-end' }"
    >
      <template #body>
        <div class="flex flex-col gap-4">
          <p class="text-sm text-surface-500 dark:text-surface-400">
            Leave the count at 1 to add a single individual, or raise it to add several at once
            sharing the same details below. They'll show up as a single grouped row until you
            change one of them.
          </p>
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
          />
          <SkinDiseaseCategorySelect v-model="batchSkinDiseaseCategoryId" />
          <DeterminationOfSheddingPropensityCategorySelect v-model="batchDeterminationCategoryId" />
          <UProgress
            v-if="savingBatch"
            :model-value="batchProgress.done"
            :max="batchProgress.total"
          />
          <UAlert v-if="batchSaveError" color="error" variant="outline" :description="batchSaveError" />
        </div>
      </template>
      <template #footer>
        <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="batchDialogVisible = false" />
        <UButton label="Add individuals" icon="i-lucide-plus" :loading="savingBatch" @click="saveBatchForm" />
      </template>
    </UModal>
  </div>
</template>
