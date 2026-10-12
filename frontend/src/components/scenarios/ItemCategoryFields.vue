<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import InlineCreatableSelect from './InlineCreatableSelect.vue'
import { itemCategoryApi, itemSubcategoryApi } from '@/api/categories'
import type { ItemSubcategory, NamedCategory } from '@/api/types'

// Item category, subcategory, and description fields shared by every "add or
// edit an item" form (in the scenario planning flow and the data-entry
// panel). A subcategory belongs to exactly one category, so the subcategory
// picker only becomes available - and only offers/creates subcategories -
// once a category has been chosen. Both pickers let the user add a new
// option inline (typing a new name and confirming), no separate dialog.
const categoryId = defineModel<string | null>('categoryId', { default: null })
const subcategoryId = defineModel<string | null>('subcategoryId', { default: null })
const description = defineModel<string | null>('description', { default: null })

const props = defineProps<{
  categoryError?: string
  subcategoryError?: string
  descriptionError?: string
}>()

const allCategories = ref<NamedCategory[]>([])
const categoriesLoading = ref(false)

const allSubcategories = ref<ItemSubcategory[]>([])
const subcategoriesLoading = ref(false)

onMounted(async () => {
  categoriesLoading.value = true
  subcategoriesLoading.value = true
  try {
    const [categories, subcategories] = await Promise.all([
      itemCategoryApi.list(),
      itemSubcategoryApi.list(),
    ])
    allCategories.value = categories
    allSubcategories.value = subcategories
  } finally {
    categoriesLoading.value = false
    subcategoriesLoading.value = false
  }
})

const availableSubcategories = computed(() =>
  allSubcategories.value.filter((s) => s.item_category_id === categoryId.value),
)

// Changing the category (including clearing it) invalidates whichever
// subcategory was picked for the previous one. Tracked against the category
// active when this instance was created (e.g. loaded from an existing
// item), so that initial value isn't mistaken for the user changing it.
const categoryIdAtStart = ref(categoryId.value)

watch(categoryId, (current) => {
  if (current !== categoryIdAtStart.value) {
    subcategoryId.value = null
    categoryIdAtStart.value = current ?? null
  }
})

async function createCategory(name: string) {
  const created = await itemCategoryApi.create({ name })
  allCategories.value = [...allCategories.value, created]
  return created
}

async function createSubcategory(name: string) {
  if (categoryId.value === null) throw new Error('No category selected')
  const created = await itemSubcategoryApi.create({ name, item_category_id: categoryId.value })
  allSubcategories.value = [...allSubcategories.value, created]
  return created
}
</script>

<template>
  <UFormField label="Item category" :error="props.categoryError">
    <InlineCreatableSelect
      v-model="categoryId"
      :options="allCategories"
      :loading="categoriesLoading"
      :create="createCategory"
      placeholder="Select or type to add a category"
    />
  </UFormField>

  <UFormField label="Item subcategory" :error="props.subcategoryError">
    <InlineCreatableSelect
      v-model="subcategoryId"
      :options="availableSubcategories"
      :loading="subcategoriesLoading"
      :disabled="categoryId === null"
      :create="createSubcategory"
      placeholder="Select or type to add a subcategory"
    />
  </UFormField>

  <UFormField label="Description" :error="props.descriptionError">
    <UTextarea v-model="description" :rows="2" class="w-full" />
  </UFormField>
</template>
