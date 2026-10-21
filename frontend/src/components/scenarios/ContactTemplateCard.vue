<script setup lang="ts">
import { computed } from 'vue'
import Panel from 'openvue/panel'
import { useConfirm } from '@/composables/useConfirm'
import SurfaceTemplateForm from './SurfaceTemplateForm.vue'
import CategorySelect from './CategorySelect.vue'
import DurationValueInput from './DurationValueInput.vue'
import FieldLabel from './FieldLabel.vue'
import { deleteSurfaceTemplate } from '@/api/surfaceTemplates'
import { emptySurfaceTemplateDraft } from './surfaceTemplateDraft'
import { usePercentModel } from './percent'
import {
  activityCategoryApi,
  pressureEstimateApi,
  frictionAppliedEstimateApi,
} from '@/api/categories'
import type { ContactTemplateDraft } from './contactTemplateDraft'

const props = defineProps<{
  index: number
  removable: boolean
  errors: Partial<Record<string, string | undefined>>
}>()

const emit = defineEmits<{ remove: [] }>()

const draft = defineModel<ContactTemplateDraft>({ required: true })
const collapsed = defineModel<boolean>('collapsed', { default: false })

const humidityPercent = usePercentModel(computed({
  get: () => draft.value.humidity,
  set: (value) => (draft.value.humidity = value),
}))

const confirm = useConfirm()

function errorFor(field: string): string | undefined {
  return props.errors[`contactTemplates[${props.index}].${field}`]
}

function confirmDeleteSurfaceTemplate(which: 'donor' | 'recipient') {
  const label = which === 'donor' ? 'donor surface' : 'recipient surface'
  confirm.require({
    message: `Delete this ${label}? You'll be able to add a new one with a different kind.`,
    header: `Delete ${label}`,
    rejectLabel: 'Cancel',
    acceptLabel: 'Delete',
    acceptColor: 'error',
    accept: () => deleteSurfaceTemplateSlot(which),
  })
}

async function deleteSurfaceTemplateSlot(which: 'donor' | 'recipient') {
  const id = which === 'donor' ? draft.value.donorSurfaceTemplateId : draft.value.recipientSurfaceTemplateId
  if (id) await deleteSurfaceTemplate(id)

  if (which === 'donor') {
    draft.value.donorSurfaceTemplate = emptySurfaceTemplateDraft()
    draft.value.donorSurfaceTemplateId = null
  } else {
    draft.value.recipientSurfaceTemplate = emptySurfaceTemplateDraft()
    draft.value.recipientSurfaceTemplateId = null
  }
}
</script>

<template>
  <Panel v-model:collapsed="collapsed" toggleable>
    <template #header>
      <span class="font-semibold">{{ draft.name || `Contact template #${props.index + 1}` }}</span>
    </template>

    <div class="flex flex-col gap-4">
      <UFormField label="Name" hint="Optional">
        <UInput v-model="draft.name" placeholder="e.g. Handshake" class="w-full" />
      </UFormField>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SurfaceTemplateForm
          v-model="draft.donorSurfaceTemplate"
          label="Donor surface"
          :locked="!!draft.donorSurfaceTemplateId && draft.donorSurfaceTemplate.kind !== null"
          @delete="confirmDeleteSurfaceTemplate('donor')"
        />
        <SurfaceTemplateForm
          v-model="draft.recipientSurfaceTemplate"
          label="Recipient surface"
          :locked="!!draft.recipientSurfaceTemplateId && draft.recipientSurfaceTemplate.kind !== null"
          @delete="confirmDeleteSurfaceTemplate('recipient')"
        />
      </div>

      <USeparator />

      <UFormField label="Duration" hint="Optional" :error="errorFor('duration')">
        <DurationValueInput v-model="draft.duration" :invalid="!!errorFor('duration')" />
      </UFormField>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <CategorySelect
          v-model="draft.pressureEstimateId"
          label="Pressure estimate"
          hint="Optional"
          :api="pressureEstimateApi"
          :allow-add="false"
        />
        <CategorySelect
          v-model="draft.frictionAppliedEstimateId"
          label="Friction applied estimate"
          hint="Optional"
          :api="frictionAppliedEstimateApi"
          :allow-add="false"
        />
      </div>

      <UFormField label="Contact area" :error="errorFor('contactArea')">
        <UFieldGroup>
          <UInputNumber v-model="draft.contactArea" orientation="vertical" class="w-full" />
          <UBadge color="neutral" variant="outline" size="lg" label="cm²" />
        </UFieldGroup>
      </UFormField>

      <CategorySelect
        v-model="draft.activityCategoryId"
        label="Activity"
        :api="activityCategoryApi"
      />

      <UFormField label="Description of contact" hint="Optional">
        <UTextarea v-model="draft.descriptionOfContact" :rows="2" class="w-full" />
      </UFormField>

      <USeparator />

      <h4 class="font-medium text-sm">Conditions during contact</h4>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <UFormField label="Temperature">
          <UFieldGroup>
            <UInputNumber v-model="draft.temperature" orientation="vertical" class="w-full" />
            <UBadge color="neutral" variant="outline" size="lg" label="°C" />
          </UFieldGroup>
        </UFormField>
        <UFormField label="Humidity" :error="errorFor('humidity')">
          <UFieldGroup>
            <UInputNumber v-model="humidityPercent" orientation="vertical" :min="0" :max="100" class="w-full" />
            <UBadge color="neutral" variant="outline" size="lg" label="%" />
          </UFieldGroup>
        </UFormField>
        <UFormField :error="errorFor('uvIrradiation')">
          <template #label>
            <FieldLabel
              label="UV irradiation"
              description="Record UV radiation exposure (type and intensity in mW/cm²) during contact. For orientation: no direct light (ambient indoor lighting like fluorescent or LED bulbs with minimal UV exposure, no direct sunlight): mostly UVA 0.0001–0.02 mW/cm²; sunlight exposure (direct or indirect exposure to natural sunlight (outdoors), intensity varies with time of day, geography, and weather condition): UVA and UVB (natural solar) 0.5–10+ mW/cm²."
            />
          </template>
          <UFieldGroup>
            <UInputNumber v-model="draft.uvIrradiation" orientation="vertical" class="w-full" />
            <UBadge color="neutral" variant="outline" size="lg" label="mW/cm²" />
          </UFieldGroup>
        </UFormField>
      </div>
      <div class="flex items-center gap-2">
        <USwitch v-model="draft.indoors" id="indoors" />
        <label for="indoors" class="text-sm">Indoors</label>
      </div>

      <USeparator />

      <UButton
        label="Remove contact template"
        icon="i-lucide-trash-2"
        color="error"
        variant="outline"
        class="self-start"
        :disabled="!props.removable"
        @click="emit('remove')"
      />
    </div>
  </Panel>
</template>
