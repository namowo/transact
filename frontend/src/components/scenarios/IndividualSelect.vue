<script setup lang="ts">
import { computed } from 'vue'
import { useIndividualOptions } from './individualOptions'

// Picks which existing Individual a surface points at. Individuals
// themselves are managed on the Individuals tab, not created from here, so
// this is a plain picker - keeping entity creation in one guided place.
// With a `scenarioId`, only individuals assigned to that scenario are offered.
const props = defineProps<{ studyId: string; scenarioId?: string | null }>()
const individualId = defineModel<string | null>({ default: null })

const { individualOptions: allIndividualOptions, loading } = useIndividualOptions(props.studyId)

const individualOptions = computed(() =>
  props.scenarioId
    ? allIndividualOptions.value.filter((individual) => individual.scenario_ids?.includes(props.scenarioId!))
    : allIndividualOptions.value,
)
</script>

<template>
  <UFormField label="Individual">
    <USelectMenu
      v-model="individualId"
      :items="individualOptions"
      value-key="id"
      placeholder="Select an individual"
      :loading="loading"
      clear
      class="w-full"
    />
    <p v-if="!loading && !individualOptions.length" class="text-sm text-muted mt-1">
      {{ scenarioId ? 'No individuals in this scenario yet.' : 'No individuals yet.' }}
      Add one on the Individuals tab first.
    </p>
  </UFormField>
</template>
