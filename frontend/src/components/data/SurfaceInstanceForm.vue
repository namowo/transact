<script setup lang="ts">
import { computed, watch } from 'vue'
import IndividualSelect from '@/components/scenarios/IndividualSelect.vue'
import CategorySelect from '@/components/scenarios/CategorySelect.vue'
import EntitySelect from '@/components/scenarios/EntitySelect.vue'
import { conditionOfItemPartCategoryApi } from '@/api/categories'
import { surfaceInstanceDetail } from './contactTemplateLabel'
import type { SurfaceInstanceDraft } from './surfaceInstanceDraft'
import type { Surface, SurfaceTemplate } from '@/api/types'

const props = defineProps<{
  studyId: string
  label: string
  template: SurfaceTemplate | null
  // Surfaces already created for earlier contacts in this study that match
  // this slot's kind (item vs individual) - offered as a "reuse" option so
  // e.g. the item a donor touched can be chained on as a recipient's
  // surface in a later contact, instead of always creating a new instance.
  existingSurfaces?: Surface[]
}>()

const draft = defineModel<SurfaceInstanceDraft>({ required: true })

function templateSummary(template: SurfaceTemplate): string {
  if (template.item_id) {
    const part = template.item_parts_category?.name
    return `Item${part ? ` — ${part}` : ''}`
  }
  const part = template.location_of_body_category?.name
  return `Individual${part ? ` — ${part}` : ''}`
}

const reusableSurfaces = computed(() => props.existingSurfaces ?? [])

const mode = computed<'new' | 'existing'>({
  get: () => (draft.value.existingSurfaceId ? 'existing' : 'new'),
  set: (value) => {
    if (value === 'new') draft.value.existingSurfaceId = null
    else draft.value.individualId = draft.value.conditionOfItemPartCategoryId = null
  },
})

// Switching templates (e.g. going back and picking a different one) can
// leave a stale existingSurfaceId pointing at a surface that no longer
// matches - reset back to "new" rather than silently keeping it.
watch(
  () => props.template,
  () => {
    draft.value.existingSurfaceId = null
  },
)
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

      <UFormField v-if="reusableSurfaces.length" label="Surface">
        <URadioGroup
          v-model="mode"
          orientation="horizontal"
          :items="[
            { label: 'New', value: 'new' },
            { label: 'Reuse an existing surface from this study', value: 'existing' },
          ]"
        />
      </UFormField>

      <template v-if="mode === 'existing'">
        <EntitySelect
          v-model="draft.existingSurfaceId"
          label="Existing surface"
          :options="reusableSurfaces"
          :option-label="(s: Surface) => surfaceInstanceDetail(s)"
        />
        <p class="text-sm text-surface-500 dark:text-surface-400 -mt-2">
          Chains this contact onto a surface already created for an earlier contact.
        </p>
      </template>

      <IndividualSelect
        v-else-if="!props.template.item_id"
        v-model="draft.individualId"
        :study-id="props.studyId"
      />

      <CategorySelect
        v-else
        v-model="draft.conditionOfItemPartCategoryId"
        label="Condition of item part"
        hint="Optional, overrides the template"
        :api="conditionOfItemPartCategoryApi"
      />
    </template>
  </div>
</template>
