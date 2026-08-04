<script setup lang="ts">
import Panel from 'primevue/panel'
import Message from 'primevue/message'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'
import InputGroup from 'primevue/inputgroup'
import InputGroupAddon from 'primevue/inputgroupaddon'
import ToggleSwitch from 'primevue/toggleswitch'
import Button from 'primevue/button'
import CategorySelect from './CategorySelect.vue'
import DurationValueInput from './DurationValueInput.vue'
import FieldLabel from './FieldLabel.vue'
import { disturbanceCategoryApi, geographicLocationCategoryApi } from '@/api/categories'
import type { PersistenceDraft } from './persistenceDraft'

const props = defineProps<{
  index: number
  removable: boolean
  errors: Partial<Record<string, string | undefined>>
}>()

const emit = defineEmits<{ remove: [] }>()

const draft = defineModel<PersistenceDraft>({ required: true })
const collapsed = defineModel<boolean>('collapsed', { default: false })

function errorFor(field: string): string | undefined {
  return props.errors[`persistencies[${props.index}].${field}`]
}
</script>

<template>
  <Panel v-model:collapsed="collapsed" toggleable>
    <template #header>
      <span class="font-semibold">Persistence #{{ props.index + 1 }}</span>
    </template>

    <div class="flex flex-col gap-4">
      <div class="flex flex-col gap-2">
        <FieldLabel
          label="Interval of persistence (Optional)"
          description="Record the time that has passed between the last contact and sampling."
        />
        <DurationValueInput
          v-model="draft.intervalOfPersistence"
          :invalid="!!errorFor('intervalOfPersistence')"
        />
        <Message v-if="errorFor('intervalOfPersistence')" severity="error" size="small" variant="simple">
          {{ errorFor('intervalOfPersistence') }}
        </Message>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div class="flex flex-col gap-2">
          <FieldLabel
            label="Temperature"
            description="Record the ambient temperature between the last contact and sampling in °C."
          />
          <InputGroup>
            <InputNumber v-model="draft.temperature" fluid />
            <InputGroupAddon>°C</InputGroupAddon>
          </InputGroup>
        </div>
        <div class="flex flex-col gap-2">
          <FieldLabel
            label="Humidity"
            description="Record the ambient relative humidity (%) between the experiment's last contact and sampling."
          />
          <InputGroup>
            <InputNumber v-model="draft.humidity" :invalid="!!errorFor('humidity')" fluid />
            <InputGroupAddon>%</InputGroupAddon>
          </InputGroup>
          <Message v-if="errorFor('humidity')" severity="error" size="small" variant="simple">
            {{ errorFor('humidity') }}
          </Message>
        </div>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div class="flex flex-col gap-2">
          <FieldLabel
            label="UV irradiation (Optional)"
            description="Record UV radiation exposure (type and intensity in mW/cm²) during the interval between the last contact and sample collection. For orientation: no direct light (ambient indoor lighting like fluorescent or LED bulbs with minimal UV exposure, no direct sunlight): mostly UVA 0.0001–0.02 mW/cm²; sunlight exposure (direct or indirect exposure to natural sunlight (outdoors), intensity varies with time of day, geography, and weather condition): UVA and UVB (natural solar) 0.5–10+ mW/cm²."
          />
          <InputGroup>
            <InputNumber v-model="draft.uvIrradiation" :invalid="!!errorFor('uvIrradiation')" fluid />
            <InputGroupAddon>mW/cm²</InputGroupAddon>
          </InputGroup>
          <Message v-if="errorFor('uvIrradiation')" severity="error" size="small" variant="simple">
            {{ errorFor('uvIrradiation') }}
          </Message>
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Duration of disturbance (Optional)</label>
          <DurationValueInput
            v-model="draft.durationOfDisturbance"
            :invalid="!!errorFor('durationOfDisturbance')"
          />
          <Message v-if="errorFor('durationOfDisturbance')" severity="error" size="small" variant="simple">
            {{ errorFor('durationOfDisturbance') }}
          </Message>
        </div>
      </div>
      <div class="flex flex-wrap gap-6">
        <div class="flex items-center gap-2">
          <ToggleSwitch v-model="draft.indoors" :input-id="`indoors-${props.index}`" />
          <label :for="`indoors-${props.index}`" class="text-sm">Indoors</label>
        </div>
        <div class="flex items-center gap-2">
          <ToggleSwitch v-model="draft.changeOverTime" :input-id="`change-over-time-${props.index}`" />
          <label :for="`change-over-time-${props.index}`" class="text-sm">Changes over time</label>
        </div>
      </div>
      <CategorySelect
        v-model="draft.disturbanceCategoryId"
        label="Disturbance"
        :api="disturbanceCategoryApi"
      />
      <CategorySelect
        v-model="draft.geographicLocationCategoryId"
        label="Geographic location"
        :api="geographicLocationCategoryApi"
      />
      <div class="flex flex-col gap-2">
        <FieldLabel
          label="Description of disturbance (Optional)"
          description="Describe if there have been other environmental conditions (e.g. rain, rapid change in temperature, etc.)"
        />
        <Textarea v-model="draft.descriptionOfDisturbance" rows="2" fluid />
      </div>

      <Button
        label="Remove persistence"
        icon="pi pi-trash"
        severity="danger"
        outlined
        class="self-start"
        :disabled="!props.removable"
        @click="emit('remove')"
      />
    </div>
  </Panel>
</template>
