<script setup lang="ts">
import Panel from 'primevue/panel'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'
import ToggleSwitch from 'primevue/toggleswitch'
import Button from 'primevue/button'
import Divider from 'primevue/divider'
import SurfaceForm from './SurfaceForm.vue'
import CategorySelect from './CategorySelect.vue'
import { activityCategoryApi } from '@/api/categories'
import type { ContactDraft } from './contactDraft'

const props = defineProps<{ index: number; removable: boolean }>()

const emit = defineEmits<{ remove: [] }>()

const draft = defineModel<ContactDraft>({ required: true })
const collapsed = defineModel<boolean>('collapsed', { default: false })
</script>

<template>
  <Panel v-model:collapsed="collapsed" toggleable>
    <template #header>
      <span class="font-semibold">Contact #{{ props.index + 1 }}</span>
    </template>

    <div class="flex flex-col gap-4">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SurfaceForm v-model="draft.donorSurface" label="Donor surface" />
        <SurfaceForm v-model="draft.recipientSurface" label="Recipient surface" />
      </div>

      <Divider />

      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Duration (seconds, Optional)</label>
          <InputNumber v-model="draft.duration" fluid />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Pressure (Optional)</label>
          <InputNumber v-model="draft.pressure" fluid />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Friction applied (Optional)</label>
          <InputNumber v-model="draft.frictionApplied" fluid />
        </div>
      </div>

      <div class="flex flex-col gap-2">
        <label class="font-medium text-sm">Contact area (Optional)</label>
        <InputNumber v-model="draft.contactArea" fluid />
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
          <label class="font-medium text-sm">Temperature (°C)</label>
          <InputNumber v-model="draft.temperature" fluid />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">Humidity (%)</label>
          <InputNumber v-model="draft.humidity" fluid />
        </div>
        <div class="flex flex-col gap-2">
          <label class="font-medium text-sm">UV irradiation</label>
          <InputNumber v-model="draft.uvIrradiation" fluid />
        </div>
      </div>
      <div class="flex items-center gap-2">
        <ToggleSwitch v-model="draft.indoors" input-id="indoors" />
        <label for="indoors" class="text-sm">Indoors</label>
      </div>

      <Divider />

      <Button
        label="Remove contact"
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
