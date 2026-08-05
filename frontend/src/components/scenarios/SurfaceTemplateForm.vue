<script setup lang="ts">
import SelectButton from 'primevue/selectbutton'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import Button from 'primevue/button'
import CategorySelect from './CategorySelect.vue'
import ItemSelect from './ItemSelect.vue'
import {
  bodyPartConditionCategoryApi,
  conditionOfItemPartCategoryApi,
  itemPartsCategoryApi,
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
  { label: 'Individual', value: 'individual' as const },
  { label: 'Item', value: 'item' as const },
]
</script>

<template>
  <div class="flex flex-col gap-4 p-4 border border-surface-200 dark:border-surface-700 rounded-lg">
    <div class="flex items-center justify-between">
      <h4 class="font-medium">{{ props.label }}</h4>
      <SelectButton
        v-model="draft.kind"
        :options="kindOptions"
        option-label="label"
        option-value="value"
        :allow-empty="false"
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
      </template>

      <template v-else>
        <ItemSelect v-model="draft.itemId" />

        <CategorySelect
          v-model="draft.itemPartsCategoryId"
          label="Item part"
          :api="itemPartsCategoryApi"
        />
        <CategorySelect
          v-model="draft.conditionOfItemPartCategoryId"
          label="Condition of item part"
          :api="conditionOfItemPartCategoryApi"
        />
      </template>

      <CategorySelect
        v-model="draft.surfaceMaterialCategoryId"
        label="Surface material"
        :api="surfaceMaterialCategoryApi"
      />
      <CategorySelect
        v-model="draft.sourceOfDnaCategoryId"
        label="Source of DNA"
        :api="sourceOfDnaCategoryApi"
      />

      <div class="flex flex-wrap gap-6">
        <div class="flex items-center gap-2">
          <ToggleSwitch v-model="draft.backgroundDna" input-id="bg-dna" />
          <label for="bg-dna" class="text-sm">Background DNA present</label>
        </div>
        <div class="flex items-center gap-2">
          <ToggleSwitch v-model="draft.prevalence" input-id="prevalence" />
          <label for="prevalence" class="text-sm">Prevalence</label>
        </div>
      </div>

      <div class="flex flex-col gap-2">
        <label class="font-medium text-sm">Further description (Optional)</label>
        <Textarea v-model="draft.furtherDescription" rows="2" fluid />
      </div>
    </template>

    <Button
      v-if="props.locked"
      :label="`Delete ${props.label.toLowerCase()}`"
      icon="pi pi-trash"
      severity="danger"
      outlined
      size="small"
      class="self-start"
      @click="emit('delete')"
    />
  </div>
</template>
