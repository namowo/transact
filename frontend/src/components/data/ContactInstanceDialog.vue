<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import SurfaceInstanceForm from './SurfaceInstanceForm.vue'
import IndividualMultiSelect from '@/components/scenarios/IndividualMultiSelect.vue'
import {
  emptyContactInstanceDraft,
  saveContactInstanceDraft,
  saveContactInstanceBatch,
} from './contactInstanceDraft'
import { templateName, surfaceLabel, surfaceIcon, surfaceDetail } from './contactTemplateLabel'
import type { ContactInstanceDraft } from './contactInstanceDraft'
import type { Contact, ContactTemplate, Surface } from '@/api/types'

const props = defineProps<{
  studyId: string
  contactTemplates: ContactTemplate[]
  // Actual contacts already recorded for this study, used to offer their
  // surfaces for reuse when chaining a new contact onto one of them.
  contacts?: Contact[]
}>()
const visible = defineModel<boolean>('visible', { required: true })

const emit = defineEmits<{ saved: [contacts: Contact[]] }>()

const draft = ref<ContactInstanceDraft>(emptyContactInstanceDraft())
const submitting = ref(false)
const submitError = ref('')
const filter = ref('')
const step = ref<'template' | 'details'>('template')
const batchIndividualIds = ref<string[]>([])

watch(visible, (isVisible) => {
  if (isVisible) {
    draft.value = emptyContactInstanceDraft()
    submitError.value = ''
    filter.value = ''
    step.value = 'template'
    batchIndividualIds.value = []
  }
})

// Batching (one contact per individual, sharing the same item) only makes
// sense when exactly one side of the template is an individual slot and the
// other is an item slot. If both sides are individuals, each pairing has to
// be picked by hand; if both are items, there's nothing to batch over.
function individualSideOf(template: ContactTemplate): 'donor' | 'recipient' | null {
  const donorIsIndividual = !template.donor_surface_template?.item_id
  const recipientIsIndividual = !template.recipient_surface_template?.item_id
  if (donorIsIndividual && !recipientIsIndividual) return 'donor'
  if (recipientIsIndividual && !donorIsIndividual) return 'recipient'
  return null
}

const filteredTemplates = computed(() => {
  const needle = filter.value.trim().toLowerCase()
  if (!needle) return props.contactTemplates
  return props.contactTemplates.filter((template) => {
    const haystack = [
      templateName(template),
      surfaceLabel(template.donor_surface_template),
      surfaceLabel(template.recipient_surface_template),
      template.activity_category?.name ?? '',
    ]
      .join(' ')
      .toLowerCase()
    return haystack.includes(needle)
  })
})

function selectTemplate(template: ContactTemplate) {
  draft.value.contactTemplateId = template.id
  step.value = 'details'
}

const selectedTemplate = computed(
  () => props.contactTemplates.find((t) => t.id === draft.value.contactTemplateId) ?? null,
)

const individualSide = computed(() =>
  selectedTemplate.value ? individualSideOf(selectedTemplate.value) : null,
)

const itemSide = computed<'donor' | 'recipient' | null>(() =>
  individualSide.value === 'donor' ? 'recipient' : individualSide.value === 'recipient' ? 'donor' : null,
)

const itemSurfaceTemplate = computed(() => {
  if (!selectedTemplate.value || !itemSide.value) return null
  return itemSide.value === 'donor'
    ? selectedTemplate.value.donor_surface_template ?? null
    : selectedTemplate.value.recipient_surface_template ?? null
})

const itemSurfaceDraft = computed({
  get: () => (itemSide.value === 'donor' ? draft.value.donorSurface : draft.value.recipientSurface),
  set: (value) => {
    if (itemSide.value === 'donor') draft.value.donorSurface = value
    else draft.value.recipientSurface = value
  },
})

// All surfaces already created for this study's actual contacts, deduped
// by id - a surface can appear as both donor and recipient across contacts.
const allExistingSurfaces = computed<Surface[]>(() => {
  const byId = new Map<string, Surface>()
  for (const contact of props.contacts ?? []) {
    if (contact.donor_surface) byId.set(contact.donor_surface.id, contact.donor_surface)
    if (contact.recipient_surface) byId.set(contact.recipient_surface.id, contact.recipient_surface)
  }
  return [...byId.values()]
})

// Surfaces offered for reuse on a given slot - only those of the same kind
// (item vs individual) as the slot's template, since a surface's shape is
// fixed by the template it instantiated.
function existingSurfacesFor(template: { item_id?: string | null } | null | undefined): Surface[] {
  if (!template) return []
  const wantsItem = !!template.item_id
  return allExistingSurfaces.value.filter((s) => !!s.surface_template?.item_id === wantsItem)
}

const donorExistingSurfaces = computed(() =>
  existingSurfacesFor(selectedTemplate.value?.donor_surface_template),
)
const recipientExistingSurfaces = computed(() =>
  existingSurfacesFor(selectedTemplate.value?.recipient_surface_template),
)
const itemExistingSurfaces = computed(() =>
  itemSide.value === 'donor' ? donorExistingSurfaces.value : recipientExistingSurfaces.value,
)

function backToTemplateStep() {
  step.value = 'template'
}

const breadcrumbItems = computed(() => [
  { label: 'Choose template', onClick: backToTemplateStep },
  ...(selectedTemplate.value
    ? [{ label: templateName(selectedTemplate.value) }]
    : []),
])

const canSave = computed(() => {
  if (!selectedTemplate.value) return false
  return individualSide.value ? batchIndividualIds.value.length > 0 : true
})

async function save() {
  if (!selectedTemplate.value) return
  submitting.value = true
  submitError.value = ''
  try {
    if (individualSide.value) {
      const contacts = await saveContactInstanceBatch(
        draft.value,
        selectedTemplate.value,
        individualSide.value,
        batchIndividualIds.value,
        allExistingSurfaces.value,
      )
      emit('saved', contacts)
    } else {
      const contact = await saveContactInstanceDraft(
        draft.value,
        selectedTemplate.value,
        allExistingSurfaces.value,
      )
      emit('saved', [contact])
    }
    visible.value = false
  } catch {
    submitError.value = 'Could not save these contacts. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <UModal
    v-model:open="visible"
    title="Add actual contact"
    :ui="{ content: 'max-w-3xl', footer: 'justify-end' }"
  >
    <template #body>
      <div class="flex flex-col gap-4">
        <UBreadcrumb v-if="step === 'details'" :items="breadcrumbItems" />

        <div v-if="step === 'template'" class="flex flex-col gap-2">
          <p class="text-sm text-muted">
            Pick which contact template this actual contact is based on. Click a row to continue.
          </p>
          <UInput
            v-model="filter"
            type="text"
            icon="i-lucide-search"
            placeholder="Search contact templates"
            class="w-full"
          />
          <div class="border border-default rounded-md overflow-hidden">
            <DataTable
              :value="filteredTemplates"
              dataKey="id"
              scrollable
              scrollHeight="20rem"
              :row-class="() => 'cursor-pointer hover:bg-elevated group'"
              @row-click="({ data }: { data: ContactTemplate }) => selectTemplate(data)"
            >
              <template #empty>No contact templates match your search.</template>
              <Column header="Name">
                <template #body="{ data }">{{ templateName(data) }}</template>
              </Column>
              <Column header="Donor">
                <template #body="{ data }">
                  <span class="flex items-center gap-1.5">
                    <UIcon
                      v-if="surfaceIcon(data.donor_surface_template)"
                      :name="surfaceIcon(data.donor_surface_template)!"
                      class="shrink-0"
                    />
                    {{ surfaceDetail(data.donor_surface_template) }}
                  </span>
                </template>
              </Column>
              <Column header="Recipient">
                <template #body="{ data }">
                  <span class="flex items-center gap-1.5">
                    <UIcon
                      v-if="surfaceIcon(data.recipient_surface_template)"
                      :name="surfaceIcon(data.recipient_surface_template)!"
                      class="shrink-0"
                    />
                    {{ surfaceDetail(data.recipient_surface_template) }}
                  </span>
                </template>
              </Column>
              <Column header="Activity">
                <template #body="{ data }">{{ data.activity_category?.name ?? '—' }}</template>
              </Column>
              <Column header="" style="width: 2.5rem">
                <template #body>
                  <UIcon
                    name="i-lucide-chevron-right"
                    class="text-dimmed group-hover:text-default"
                  />
                </template>
              </Column>
            </DataTable>
          </div>
        </div>

        <template v-else-if="selectedTemplate && individualSide">
          <SurfaceInstanceForm
            v-model="itemSurfaceDraft"
            :study-id="props.studyId"
            :label="itemSide === 'donor' ? 'Donor' : 'Recipient'"
            :template="itemSurfaceTemplate"
            :existing-surfaces="itemExistingSurfaces"
          />
          <UFormField
            :label="individualSide === 'donor' ? 'Donors' : 'Recipients'"
            hint="One contact is created per selected individual"
          >
            <IndividualMultiSelect v-model="batchIndividualIds" :study-id="props.studyId" />
          </UFormField>
        </template>

        <template v-else-if="selectedTemplate">
          <SurfaceInstanceForm
            v-model="draft.donorSurface"
            :study-id="props.studyId"
            label="Donor"
            :template="selectedTemplate.donor_surface_template ?? null"
            :existing-surfaces="donorExistingSurfaces"
          />
          <SurfaceInstanceForm
            v-model="draft.recipientSurface"
            :study-id="props.studyId"
            label="Recipient"
            :template="selectedTemplate.recipient_surface_template ?? null"
            :existing-surfaces="recipientExistingSurfaces"
          />
        </template>

        <UAlert v-if="submitError" color="error" variant="outline" :description="submitError" />
      </div>
    </template>
    <template #footer>
      <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="visible = false" />
      <UButton
        v-if="step === 'details'"
        label="Back"
        icon="i-lucide-arrow-left"
        variant="ghost"
        @click="backToTemplateStep"
      />
      <UButton
        v-if="step === 'details'"
        :label="individualSide && batchIndividualIds.length > 1
          ? `Save ${batchIndividualIds.length} contacts`
          : 'Save'"
        icon="i-lucide-save"
        :loading="submitting"
        :disabled="!canSave"
        @click="save"
      />
    </template>
  </UModal>
</template>
