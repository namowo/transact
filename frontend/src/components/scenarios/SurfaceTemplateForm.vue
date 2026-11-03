<script setup lang="ts">
import { ref } from 'vue'
import CategorySelect from './CategorySelect.vue'
import ItemSelect from './ItemSelect.vue'
import ItemPartSelect from './ItemPartSelect.vue'
import {
  bodyPartConditionCategoryApi,
  conditionOfItemPartCategoryApi,
  itemSurfaceMaterialCategoryApi,
  locationOfBodyCategoryApi,
  sourceOfDnaCategoryApi,
  surfaceMaterialCategoryApi,
} from '@/api/categories'
import type { SurfaceTemplateDraft } from './surfaceTemplateDraft'

// Locked once this surface template has been saved (has an id) and a kind
// was chosen - switching Individual/Item on a saved record would leave
// stale data in the other kind's fields. To change the kind, the whole
// surface template must be deleted and re-created via the delete button.
const props = defineProps<{ label: string; locked: boolean }>()

const emit = defineEmits<{ delete: [] }>()

const draft = defineModel<SurfaceTemplateDraft>({ required: true })

const kindOptions = [
  { label: 'Individual', value: 'individual' as const, icon: 'i-lucide-user' },
  { label: 'Item', value: 'item' as const, icon: 'i-lucide-package' },
]

// Derived from whichever item is selected, not persisted on the draft -
// scopes the Item part picker to that item's category.
const selectedItemCategoryId = ref<string | null>(null)
</script>

<template>
  <div class="flex flex-col gap-4 p-4 border border-surface-200 dark:border-surface-700 rounded-lg">
    <div class="flex items-center justify-between">
      <h4 class="font-medium">{{ props.label }}</h4>
      <URadioGroup
        v-model="draft.kind"
        :items="kindOptions"
        indicator="hidden"
        orientation="horizontal"
        variant="table"
        :disabled="props.locked"
      />
    </div>

    <p v-if="props.locked" class="text-sm text-surface-500 dark:text-surface-400">
      Individual/Item can't be changed after saving. Delete this surface to start over with a
      different kind.
    </p>

    <p v-if="draft.kind === null" class="text-sm text-surface-500 dark:text-surface-400">
      Choose Individual or Item to continue.
    </p>

    <template v-else>
      <template v-if="draft.kind === 'individual'">
        <p class="text-sm text-surface-500 dark:text-surface-400">
          The individual itself is chosen later, during data entry.
        </p>

        <CategorySelect
          v-model="draft.locationOfBodyCategoryId"
          label="Location on body"
          :api="locationOfBodyCategoryApi"
        />
        <CategorySelect
          v-model="draft.bodyPartConditionCategoryId"
          label="Body part condition"
          :api="bodyPartConditionCategoryApi"
        />
        <CategorySelect
          v-model="draft.sourceOfDnaCategoryIds"
          label="Source of DNA"
          multiple
          :api="sourceOfDnaCategoryApi"
        />
      </template>

      <template v-else>
        <ItemSelect v-model="draft.itemId" v-model:item-category-id="selectedItemCategoryId" />

        <p v-if="!draft.itemId" class="text-sm text-surface-500 dark:text-surface-400">
          Select an item above to continue.
        </p>

        <ItemPartSelect
          v-model="draft.itemPartsCategoryId"
          :item-category-id="selectedItemCategoryId"
          :disabled="!draft.itemId"
        />
        <CategorySelect
          v-model="draft.conditionOfItemPartCategoryId"
          label="Condition of item part"
          :api="conditionOfItemPartCategoryApi"
          :disabled="!draft.itemId"
        />
        <CategorySelect
          v-model="draft.itemSurfaceMaterialCategoryId"
          label="Surface material"
          :api="itemSurfaceMaterialCategoryApi"
          :disabled="!draft.itemId"
        />
      </template>

      <CategorySelect
        v-if="draft.kind === 'individual'"
        v-model="draft.surfaceMaterialCategoryId"
        label="Surface material"
        :api="surfaceMaterialCategoryApi"
      />

      <div class="flex items-center gap-2">
        <USwitch v-model="draft.backgroundDna" id="bg-dna" />
        <label for="bg-dna" class="text-sm">Background DNA present</label>
      </div>

      <UFormField label="Further description" hint="Optional">
        <UTextarea v-model="draft.furtherDescription" :rows="2" class="w-full" />
      </UFormField>
    </template>

    <UButton
      v-if="props.locked"
      :label="`Delete ${props.label.toLowerCase()}`"
      icon="i-lucide-trash-2"
      color="error"
      variant="outline"
      size="sm"
      class="self-start"
      @click="emit('delete')"
    />
  </div>
</template>
