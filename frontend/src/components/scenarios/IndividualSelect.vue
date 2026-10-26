<script setup lang="ts">
import { useIndividualOptions } from './individualOptions'

// Picks which existing Individual a surface points at. Individuals
// themselves are managed on the Individuals tab, not created from here, so
// this is a plain picker - keeping entity creation in one guided place.
const props = defineProps<{ studyId: string }>()
const individualId = defineModel<string | null>({ default: null })

const { individualOptions, loading } = useIndividualOptions(props.studyId)
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
      No individuals yet. Add one on the Individuals tab first.
    </p>
  </UFormField>
</template>
