<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Message from 'primevue/message'
import EntitySelect from '@/components/scenarios/EntitySelect.vue'
import SurfaceInstanceForm from './SurfaceInstanceForm.vue'
import { emptyContactInstanceDraft, saveContactInstanceDraft } from './contactInstanceDraft'
import type { ContactInstanceDraft } from './contactInstanceDraft'
import type { Contact, ContactTemplate } from '@/api/types'

const props = defineProps<{ contactTemplates: ContactTemplate[] }>()
const visible = defineModel<boolean>('visible', { required: true })

const emit = defineEmits<{ saved: [contact: Contact] }>()

const draft = ref<ContactInstanceDraft>(emptyContactInstanceDraft())
const submitting = ref(false)
const submitError = ref('')

watch(visible, (isVisible) => {
  if (isVisible) {
    draft.value = emptyContactInstanceDraft()
    submitError.value = ''
  }
})

function templateLabel(template: ContactTemplate): string {
  const donor = template.donor_surface_template?.item_id ? 'Item' : 'Individual'
  const recipient = template.recipient_surface_template?.item_id ? 'Item' : 'Individual'
  return `Contact template #${template.id} (${donor} → ${recipient})`
}

const selectedTemplate = computed(
  () => props.contactTemplates.find((t) => t.id === draft.value.contactTemplateId) ?? null,
)

async function save() {
  if (!selectedTemplate.value) return
  submitting.value = true
  submitError.value = ''
  try {
    const contact = await saveContactInstanceDraft(draft.value, selectedTemplate.value)
    emit('saved', contact)
    visible.value = false
  } catch {
    submitError.value = 'Could not save this contact. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <Dialog
    v-model:visible="visible"
    header="Add actual contact"
    modal
    :style="{ width: '36rem' }"
  >
    <div class="flex flex-col gap-4">
      <EntitySelect
        v-model="draft.contactTemplateId"
        label="Contact template"
        :options="props.contactTemplates"
        :option-label="templateLabel"
      />

      <template v-if="selectedTemplate">
        <SurfaceInstanceForm
          v-model="draft.donorSurface"
          label="Donor"
          :template="selectedTemplate.donor_surface_template ?? null"
        />
        <SurfaceInstanceForm
          v-model="draft.recipientSurface"
          label="Recipient"
          :template="selectedTemplate.recipient_surface_template ?? null"
        />
      </template>

      <Message v-if="submitError" severity="error" size="small">{{ submitError }}</Message>
    </div>
    <template #footer>
      <Button label="Cancel" text @click="visible = false" />
      <Button
        label="Save"
        :loading="submitting"
        :disabled="!selectedTemplate"
        @click="save"
      />
    </template>
  </Dialog>
</template>
