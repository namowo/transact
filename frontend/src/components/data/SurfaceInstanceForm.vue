<script setup lang="ts">
import IndividualSelect from '@/components/scenarios/IndividualSelect.vue'
import CategorySelect from '@/components/scenarios/CategorySelect.vue'
import { conditionOfItemPartCategoryApi } from '@/api/categories'
import type { SurfaceInstanceDraft } from './surfaceInstanceDraft'
import type { SurfaceTemplate } from '@/api/types'

const props = defineProps<{ label: string; template: SurfaceTemplate | null }>()

const draft = defineModel<SurfaceInstanceDraft>({ required: true })

function templateSummary(template: SurfaceTemplate): string {
  if (template.item_id) {
    const part = template.item_parts_category?.name
    return `Item${part ? ` — ${part}` : ''}`
  }
  const part = template.location_of_body_category?.name
  return `Individual${part ? ` — ${part}` : ''}`
}
</script>

<template>
  <div class="flex flex-col gap-4 p-4 border border-surface-200 dark:border-surface-700 rounded-lg">
    <h4 class="font-medium">{{ props.label }}</h4>

    <p v-if="!props.template" class="text-sm text-surface-500 dark:text-surface-400">
      This contact template has no {{ props.label.toLowerCase() }} defined.
    </p>

    <template v-else>
      <p class="text-sm text-surface-500 dark:text-surface-400">
        {{ templateSummary(props.template) }}
      </p>

      <IndividualSelect v-if="!props.template.item_id" v-model="draft.individualId" />

      <CategorySelect
        v-else
        v-model="draft.conditionOfItemPartCategoryId"
        label="Condition of item part (Optional, overrides the template)"
        :api="conditionOfItemPartCategoryApi"
      />
    </template>
  </div>
</template>
