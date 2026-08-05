<script setup lang="ts">
import Panel from 'primevue/panel'
import Message from 'primevue/message'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'
import InputGroup from 'primevue/inputgroup'
import InputGroupAddon from 'primevue/inputgroupaddon'
import ToggleSwitch from 'primevue/toggleswitch'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import CategorySelect from './CategorySelect.vue'
import DurationValueInput from './DurationValueInput.vue'
import FieldLabel from './FieldLabel.vue'
import { disturbanceCategoryApi, geographicLocationCategoryApi } from '@/api/categories'
import type { PersistenceDraft } from './persistenceDraft'

const props = defineProps<{
  index: number
  removable: boolean
  editable: boolean
  errors: Partial<Record<string, string | undefined>>
}>()

const emit = defineEmits<{ remove: [] }>()

const draft = defineModel<PersistenceDraft>({ required: true })
const collapsed = defineModel<boolean>('collapsed', { default: false })

function errorFor(field: string): string | undefined {
  return props.errors[`persistencies[${props.index}].${field}`]
}

function formatDuration(seconds: number | null): string | null {
  if (seconds == null) return null
  const units: [string, number][] = [
    ['y', 31536000],
    ['d', 86400],
    ['h', 3600],
    ['min', 60],
    ['s', 1],
  ]
  const parts: string[] = []
  let remainder = seconds
  for (const [label, factor] of units) {
    const amount = Math.trunc(remainder / factor)
    if (amount > 0) parts.push(`${amount}${label}`)
    remainder -= amount * factor
  }
  return parts.length ? parts.join(' ') : '0s'
}
</script>

<template>
  <Panel v-if="!props.editable" toggleable :collapsed="collapsed" @update:collapsed="collapsed = $event">
    <template #header>
      <span class="font-semibold">{{ draft.name || `Persistence #${props.index + 1}` }}</span>
      <Tag value="From another study" severity="info" />
    </template>

    <div class="flex flex-col gap-3 text-sm">
      <p class="text-surface-500 dark:text-surface-400">
        This persistence was created for another study, so it can only be edited there. You can
        still link or remove it here.
      </p>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2">
        <div v-if="draft.intervalOfPersistence != null">
          <span class="font-medium">Interval of persistence:</span>
          {{ formatDuration(draft.intervalOfPersistence) }}
        </div>
        <div v-if="draft.temperature != null">
          <span class="font-medium">Temperature:</span> {{ draft.temperature }} °C
        </div>
        <div v-if="draft.humidity != null">
          <span class="font-medium">Humidity:</span> {{ draft.humidity }} %
        </div>
        <div v-if="draft.uvIrradiation != null">
          <span class="font-medium">UV irradiation:</span> {{ draft.uvIrradiation }} mW/cm²
        </div>
        <div v-if="draft.durationOfDisturbance != null">
          <span class="font-medium">Duration of disturbance:</span>
          {{ formatDuration(draft.durationOfDisturbance) }}
        </div>
        <div v-if="draft.indoors">Indoors</div>
        <div v-if="draft.changeOverTime">Changes over time</div>
      </div>
      <p v-if="draft.descriptionOfDisturbance" class="text-surface-500 dark:text-surface-400">
        {{ draft.descriptionOfDisturbance }}
      </p>

      <Button
        label="Remove from this scenario"
        icon="pi pi-times"
        severity="warn"
        outlined
        class="self-start"
        @click="emit('remove')"
      />
    </div>
  </Panel>

  <Panel v-else v-model:collapsed="collapsed" toggleable>
    <template #header>
      <span class="font-semibold">{{ draft.name || `Persistence #${props.index + 1}` }}</span>
    </template>

    <div class="flex flex-col gap-4">
      <div class="flex flex-col gap-2">
        <label class="font-medium text-sm">Name (Optional)</label>
        <InputText v-model="draft.name" placeholder="e.g. Winter, Summer" fluid />
      </div>
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
