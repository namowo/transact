<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import Message from 'primevue/message'
import Divider from 'primevue/divider'
import CategorySelect from '@/components/scenarios/CategorySelect.vue'
import SkinDiseaseCategorySelect from '@/components/scenarios/SkinDiseaseCategorySelect.vue'
import DeterminationOfSheddingPropensityCategorySelect from '@/components/scenarios/DeterminationOfSheddingPropensityCategorySelect.vue'
import { sexApi, dnaSheddingPropensityCategoryApi, itemCategoryApi, itemSubcategoryApi } from '@/api/categories'
import { createIndividual, listIndividuals, updateIndividual } from '@/api/individuals'
import { createItem, listItems, updateItem } from '@/api/items'
import type { Individual, Item } from '@/api/types'

const individuals = ref<Individual[]>([])
const items = ref<Item[]>([])
const loading = ref(false)
const loadError = ref('')

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const [individualResults, itemResults] = await Promise.all([listIndividuals(), listItems()])
    individuals.value = individualResults.sort((a, b) => a.id - b.id)
    items.value = itemResults.sort((a, b) => a.id - b.id)
  } catch {
    loadError.value = 'Could not load individuals and items. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

function individualLabel(individual: Individual): string {
  const position = individuals.value.findIndex((candidate) => candidate.id === individual.id)
  return `Individual ${position + 1}`
}

function itemLabel(item: Item): string {
  const position = items.value.findIndex((candidate) => candidate.id === item.id)
  return `Item ${position + 1}`
}

// -- Individuals dialog --

interface IndividualFormState {
  sexId: number | null
  age: number | null
  dnaSheddingPropensityCategoryId: number | null
  skinDiseaseCategoryId: number | null
  determinationCategoryId: number | null
}

function emptyIndividualForm(individual: Individual | null): IndividualFormState {
  return {
    sexId: individual?.sex_id ?? null,
    age: individual?.age ?? null,
    dnaSheddingPropensityCategoryId: individual?.dna_shedding_propensity_category_id ?? null,
    skinDiseaseCategoryId: individual?.skin_disease_category_id ?? null,
    determinationCategoryId: individual?.determination_of_shedding_propensity_category_id ?? null,
  }
}

const individualSchema = yup.object({
  sexId: yup.number().nullable().defined(),
  age: yup.number().nullable().min(0, 'Age must be zero or greater.'),
  dnaSheddingPropensityCategoryId: yup.number().nullable().defined(),
  skinDiseaseCategoryId: yup.number().nullable().defined(),
  determinationCategoryId: yup.number().nullable().defined(),
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

const [individualSexId] = defineIndividualField('sexId')
const [individualAge] = defineIndividualField('age')
const [individualDnaSheddingPropensityCategoryId] = defineIndividualField(
  'dnaSheddingPropensityCategoryId',
)
const [individualSkinDiseaseCategoryId] = defineIndividualField('skinDiseaseCategoryId')
const [individualDeterminationCategoryId] = defineIndividualField('determinationCategoryId')

const individualDialogVisible = ref(false)
const editingIndividualId = ref<number | null>(null)
const savingIndividual = ref(false)
const individualSaveError = ref('')

function openCreateIndividualDialog() {
  editingIndividualId.value = null
  resetIndividualForm({ values: emptyIndividualForm(null) })
  individualSaveError.value = ''
  individualDialogVisible.value = true
}

function openEditIndividualDialog(individual: Individual) {
  editingIndividualId.value = individual.id
  resetIndividualForm({ values: emptyIndividualForm(individual) })
  individualSaveError.value = ''
  individualDialogVisible.value = true
}

const saveIndividualForm = handleIndividualSubmit(async (values) => {
  savingIndividual.value = true
  individualSaveError.value = ''
  try {
    const payload = {
      sex_id: values.sexId,
      age: values.age,
      dna_shedding_propensity_category_id: values.dnaSheddingPropensityCategoryId,
      skin_disease_category_id: values.skinDiseaseCategoryId,
      determination_of_shedding_propensity_category_id: values.determinationCategoryId,
    }
    if (editingIndividualId.value === null) {
      const created = await createIndividual(payload)
      individuals.value = [...individuals.value, created]
    } else {
      const updated = await updateIndividual(editingIndividualId.value, payload)
      individuals.value = individuals.value.map((candidate) =>
        candidate.id === updated.id ? updated : candidate,
      )
    }
    individualDialogVisible.value = false
  } catch {
    individualSaveError.value = 'Could not save this individual. Please try again.'
  } finally {
    savingIndividual.value = false
  }
})

// -- Items dialog --

interface ItemFormState {
  itemCategoryId: number | null
  itemSubcategoryId: number | null
  description: string | null
}

function emptyItemForm(item: Item | null): ItemFormState {
  return {
    itemCategoryId: item?.item_category_id ?? null,
    itemSubcategoryId: item?.item_subcategory_id ?? null,
    description: item?.description ?? null,
  }
}

const itemSchema = yup.object({
  itemCategoryId: yup.number().nullable().defined(),
  itemSubcategoryId: yup.number().nullable().defined(),
  description: yup.string().nullable().defined(),
})

const {
  defineField: defineItemField,
  handleSubmit: handleItemSubmit,
  resetForm: resetItemForm,
} = useForm<ItemFormState>({
  validationSchema: itemSchema,
  initialValues: emptyItemForm(null),
})

const [itemCategoryId] = defineItemField('itemCategoryId')
const [itemSubcategoryId] = defineItemField('itemSubcategoryId')
const [itemDescription] = defineItemField('description')

const itemDialogVisible = ref(false)
const editingItemId = ref<number | null>(null)
const savingItem = ref(false)
const itemSaveError = ref('')

function openCreateItemDialog() {
  editingItemId.value = null
  resetItemForm({ values: emptyItemForm(null) })
  itemSaveError.value = ''
  itemDialogVisible.value = true
}

function openEditItemDialog(item: Item) {
  editingItemId.value = item.id
  resetItemForm({ values: emptyItemForm(item) })
  itemSaveError.value = ''
  itemDialogVisible.value = true
}

const saveItemForm = handleItemSubmit(async (values) => {
  savingItem.value = true
  itemSaveError.value = ''
  try {
    const payload = {
      item_category_id: values.itemCategoryId,
      item_subcategory_id: values.itemSubcategoryId,
      description: values.description,
    }
    if (editingItemId.value === null) {
      const created = await createItem(payload)
      items.value = [...items.value, created]
    } else {
      const updated = await updateItem(editingItemId.value, payload)
      items.value = items.value.map((candidate) => (candidate.id === updated.id ? updated : candidate))
    }
    itemDialogVisible.value = false
  } catch {
    itemSaveError.value = 'Could not save this item. Please try again.'
  } finally {
    savingItem.value = false
  }
})
</script>

<template>
  <div class="flex flex-col gap-8">
    <Message v-if="loadError" severity="error" size="small">{{ loadError }}</Message>

    <div class="flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <h4 class="font-medium">Individuals</h4>
        <Button
          label="Add individual"
          icon="pi pi-plus"
          outlined
          @click="openCreateIndividualDialog"
        />
      </div>
      <div class="overflow-x-auto">
        <DataTable :value="individuals" :loading="loading" data-key="id">
          <Column header="Name">
            <template #body="{ data }">{{ individualLabel(data) }}</template>
          </Column>
          <Column header="Sex">
            <template #body="{ data }">{{ data.sex?.name ?? '—' }}</template>
          </Column>
          <Column field="age" header="Age" />
          <Column header="Skin disease">
            <template #body="{ data }">{{ data.skin_disease_category?.name ?? '—' }}</template>
          </Column>
          <Column header="" style="width: 4rem">
            <template #body="{ data }">
              <Button
                icon="pi pi-pencil"
                text
                rounded
                aria-label="Edit individual"
                @click="openEditIndividualDialog(data)"
              />
            </template>
          </Column>
        </DataTable>
      </div>
    </div>

    <Divider />

    <div class="flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <h4 class="font-medium">Items</h4>
        <Button label="Add item" icon="pi pi-plus" outlined @click="openCreateItemDialog" />
      </div>
      <div class="overflow-x-auto">
        <DataTable :value="items" :loading="loading" data-key="id">
          <Column header="Name">
            <template #body="{ data }">{{ itemLabel(data) }}</template>
          </Column>
          <Column header="Category">
            <template #body="{ data }">{{ data.item_category?.name ?? '—' }}</template>
          </Column>
          <Column header="Subcategory">
            <template #body="{ data }">{{ data.item_subcategory?.name ?? '—' }}</template>
          </Column>
          <Column field="description" header="Description" />
          <Column header="" style="width: 4rem">
            <template #body="{ data }">
              <Button
                icon="pi pi-pencil"
                text
                rounded
                aria-label="Edit item"
                @click="openEditItemDialog(data)"
              />
            </template>
          </Column>
        </DataTable>
      </div>
    </div>

    <Dialog
      v-model:visible="individualDialogVisible"
      :header="editingIndividualId === null ? 'Add individual' : 'Edit individual'"
      modal
      :style="{ width: '28rem' }"
    >
      <div class="flex flex-col gap-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <CategorySelect v-model="individualSexId" label="Sex (Optional)" :api="sexApi" />
          <div class="flex flex-col gap-2">
            <label class="font-medium text-sm">Age (Optional)</label>
            <InputNumber v-model="individualAge" :invalid="!!individualErrors.age" fluid />
            <Message v-if="individualErrors.age" severity="error" size="small" variant="simple">
              {{ individualErrors.age }}
            </Message>
          </div>
        </div>
        <CategorySelect
          v-model="individualDnaSheddingPropensityCategoryId"
          label="DNA shedding propensity (Optional)"
          :api="dnaSheddingPropensityCategoryApi"
        />
        <SkinDiseaseCategorySelect v-model="individualSkinDiseaseCategoryId" />
        <DeterminationOfSheddingPropensityCategorySelect
          v-model="individualDeterminationCategoryId"
        />
        <Message v-if="individualSaveError" severity="error" size="small">
          {{ individualSaveError }}
        </Message>
      </div>
      <template #footer>
        <Button label="Cancel" text @click="individualDialogVisible = false" />
        <Button label="Save" :loading="savingIndividual" @click="saveIndividualForm" />
      </template>
    </Dialog>

    <Dialog
      v-model:visible="itemDialogVisible"
      :header="editingItemId === null ? 'Add item' : 'Edit item'"
      modal
      :style="{ width: '28rem' }"
    >
      <div class="flex flex-col gap-4">
        <CategorySelect v-model="itemCategoryId" label="Item category" :api="itemCategoryApi" />
        <CategorySelect
          v-model="itemSubcategoryId"
          label="Item subcategory"
          :api="itemSubcategoryApi"
        />
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Description (Optional)</label>
          <Textarea v-model="itemDescription" rows="2" fluid />
        </div>
        <Message v-if="itemSaveError" severity="error" size="small">{{ itemSaveError }}</Message>
      </div>
      <template #footer>
        <Button label="Cancel" text @click="itemDialogVisible = false" />
        <Button label="Save" :loading="savingItem" @click="saveItemForm" />
      </template>
    </Dialog>
  </div>
</template>
