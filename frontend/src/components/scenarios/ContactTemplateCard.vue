<script setup lang="ts">
import Panel from 'primevue/panel'
import Message from 'primevue/message'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'
import InputGroup from 'primevue/inputgroup'
import InputGroupAddon from 'primevue/inputgroupaddon'
import ToggleSwitch from 'primevue/toggleswitch'
import Button from 'primevue/button'
import Divider from 'primevue/divider'
import { useConfirm } from 'primevue/useconfirm'
import SurfaceTemplateForm from './SurfaceTemplateForm.vue'
import CategorySelect from './CategorySelect.vue'
import DurationValueInput from './DurationValueInput.vue'
import FieldLabel from './FieldLabel.vue'
import { deleteSurfaceTemplate } from '@/api/surfaceTemplates'
import { emptySurfaceTemplateDraft } from './surfaceTemplateDraft'
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

const confirm = useConfirm()

function errorFor(field: string): string | undefined {
  return props.errors[`contactTemplates[${props.index}].${field}`]
}

function confirmDeleteSurfaceTemplate(which: 'donor' | 'recipient') {
  const label = which === 'donor' ? 'donor surface' : 'recipient surface'
  confirm.require({
    message: `Delete this ${label}? You'll be able to add a new one with a different kind.`,
    header: `Delete ${label}`,
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: 'Cancel', severity: 'secondary', text: true },
    acceptProps: { label: 'Delete', severity: 'danger' },
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
      <span class="font-semibold">Contact template #{{ props.index + 1 }}</span>
    </template>

    <div class="flex flex-col gap-4">
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

      <Divider />

      <div class="flex flex-col gap-2">
        <label class="font-medium text-sm">Duration (Optional)</label>
        <DurationValueInput v-model="draft.duration" :invalid="!!errorFor('duration')" />
        <Message v-if="errorFor('duration')" severity="error" size="small" variant="simple">
          {{ errorFor('duration') }}
        </Message>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <CategorySelect
          v-model="draft.pressureEstimateId"
          label="Pressure estimate (Optional)"
          :api="pressureEstimateApi"
          :allow-add="false"
        />
        <CategorySelect
          v-model="draft.frictionAppliedEstimateId"
          label="Friction applied estimate (Optional)"
          :api="frictionAppliedEstimateApi"
          :allow-add="false"
        />
      </div>

      <div class="flex flex-col gap-2">
        <label class="font-medium text-sm">Contact area</label>
        <InputGroup>
          <InputNumber v-model="draft.contactArea" :invalid="!!errorFor('contactArea')" fluid />
          <InputGroupAddon>cm²</InputGroupAddon>
        </InputGroup>
        <Message v-if="errorFor('contactArea')" severity="error" size="small" variant="simple">
          {{ errorFor('contactArea') }}
        </Message>
      </div>

      <CategorySelect
        v-model="draft.activityCategoryId"
        label="Activity"
        :api="activityCategoryApi"
      />

      <div class="flex flex-col gap-2">
        <label class="font-medium text-sm">Description of contact (Optional)</label>
        <Textarea v-model="draft.descriptionOfContact" rows="2" fluid />
      </div>

      <Divider />

      <h4 class="font-medium text-sm">Conditions during contact</h4>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Temperature</label>
          <InputGroup>
            <InputNumber v-model="draft.temperature" fluid />
            <InputGroupAddon>°C</InputGroupAddon>
          </InputGroup>
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Humidity</label>
          <InputGroup>
            <InputNumber v-model="draft.humidity" :invalid="!!errorFor('humidity')" fluid />
            <InputGroupAddon>%</InputGroupAddon>
          </InputGroup>
          <Message v-if="errorFor('humidity')" severity="error" size="small" variant="simple">
            {{ errorFor('humidity') }}
          </Message>
        </div>
        <div class="flex flex-col gap-2">
          <FieldLabel
            label="UV irradiation"
            description="Record UV radiation exposure (type and intensity in mW/cm²) during contact. For orientation: no direct light (ambient indoor lighting like fluorescent or LED bulbs with minimal UV exposure, no direct sunlight): mostly UVA 0.0001–0.02 mW/cm²; sunlight exposure (direct or indirect exposure to natural sunlight (outdoors), intensity varies with time of day, geography, and weather condition): UVA and UVB (natural solar) 0.5–10+ mW/cm²."
          />
          <InputGroup>
            <InputNumber
              v-model="draft.uvIrradiation"
              :invalid="!!errorFor('uvIrradiation')"
              fluid
            />
            <InputGroupAddon>mW/cm²</InputGroupAddon>
          </InputGroup>
          <Message v-if="errorFor('uvIrradiation')" severity="error" size="small" variant="simple">
            {{ errorFor('uvIrradiation') }}
          </Message>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <ToggleSwitch v-model="draft.indoors" input-id="indoors" />
        <label for="indoors" class="text-sm">Indoors</label>
      </div>

      <Divider />

      <Button
        label="Remove contact template"
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
