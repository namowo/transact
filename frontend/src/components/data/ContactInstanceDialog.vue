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
import type { Contact, ContactTemplate, Scenario, Surface } from '@/api/types'

const props = defineProps<{
  studyId: string
  contactTemplates: ContactTemplate[]
  // Actual contacts already recorded for this study, used to offer their
  // surfaces for reuse when chaining a new contact onto one of them.
  contacts?: Contact[]
  // Human-readable label for a contact, shared with the contact list so
  // both name the same contact the same way.
  contactLabel?: (contact: Contact) => string
  // The study's scenarios and the one currently selected on the page. When
  // no scenario is selected ("All data"), the dialog first asks which
  // scenario the contact belongs to.
  scenarios: Scenario[]
  scenarioId: string | null
}>()
const visible = defineModel<boolean>('visible', { required: true })

const emit = defineEmits<{ saved: [contacts: Contact[]] }>()

const draft = ref<ContactInstanceDraft>(emptyContactInstanceDraft())
const submitting = ref(false)
const submitError = ref('')
const filter = ref('')
const step = ref<'scenario' | 'template' | 'details'>('template')
const batchIndividualIds = ref<string[]>([])
const chosenScenarioId = ref<string | null>(null)

// The scenario step is only needed when the page isn't scoped to one already.
const needsScenarioStep = computed(() => props.scenarioId === null)

watch(visible, (isVisible) => {
  if (isVisible) {
    draft.value = emptyContactInstanceDraft()
    submitError.value = ''
    filter.value = ''
    batchIndividualIds.value = []
    chosenScenarioId.value =
      props.scenarioId ?? (props.scenarios.length === 1 ? props.scenarios[0]!.id : null)
    step.value = needsScenarioStep.value ? 'scenario' : 'template'
  }
})

const chosenScenario = computed(
  () => props.scenarios.find((scenario) => scenario.id === chosenScenarioId.value) ?? null,
)

function scenarioTemplateIds(scenario: Scenario): Set<string> {
  return new Set(scenario.contact_templates.map((template) => template.id))
}

const scenarioItems = computed(() =>
  props.scenarios.map((scenario) => {
    const count = props.contactTemplates.filter((t) => scenarioTemplateIds(scenario).has(t.id)).length
    return {
      label: scenario.name,
      description: count
        ? `${count} contact template${count === 1 ? '' : 's'}`
        : 'No contact templates planned yet',
      value: scenario.id,
      disabled: count === 0,
    }
  }),
)

// Templates and recorded contacts of the chosen scenario only.
const scopedTemplates = computed<ContactTemplate[]>(() => {
  if (!chosenScenario.value) return props.contactTemplates
  const ids = scenarioTemplateIds(chosenScenario.value)
  return props.contactTemplates.filter((template) => ids.has(template.id))
})

const scopedContacts = computed<Contact[]>(() => {
  const ids = new Set(scopedTemplates.value.map((template) => template.id))
  return (props.contacts ?? []).filter(
    (contact) => contact.contact_template_id != null && ids.has(contact.contact_template_id),
  )
})

function continueWithScenario() {
  if (!chosenScenarioId.value) return
  // A template or individuals picked for another scenario may not apply here.
  if (!scopedTemplates.value.some((t) => t.id === draft.value.contactTemplateId)) {
    draft.value = emptyContactInstanceDraft()
  }
  batchIndividualIds.value = []
  step.value = 'template'
}

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
  if (!needle) return scopedTemplates.value
  return scopedTemplates.value.filter((template) => {
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
  () => scopedTemplates.value.find((t) => t.id === draft.value.contactTemplateId) ?? null,
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
  for (const contact of scopedContacts.value) {
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
// Actual contacts of the template this one follows, offered as predecessor.
const predecessorContacts = computed<Contact[]>(() => {
  const previousId = selectedTemplate.value?.previous_contact_template_id
  if (!previousId) return []
  const followed = new Set(scopedContacts.value.map((c) => c.previous_contact_id))
  return scopedContacts.value.filter(
    (c) => c.contact_template_id === previousId && !followed.has(c.id),
  )
})

const predecessorTemplate = computed(() => {
  const previousId = selectedTemplate.value?.previous_contact_template_id
  return props.contactTemplates.find((t) => t.id === previousId) ?? null
})

const NO_PREDECESSOR = '__none__'

const predecessorItems = computed(() => [
  { label: 'None', value: NO_PREDECESSOR },
  ...predecessorContacts.value.map((c) => ({
    label: props.contactLabel?.(c) ?? c.name ?? 'Contact',
    value: c.id,
  })),
])

const itemExistingSurfaces = computed(() =>
  itemSide.value === 'donor' ? donorExistingSurfaces.value : recipientExistingSurfaces.value,
)

function backToTemplateStep() {
  step.value = 'template'
}

function backToScenarioStep() {
  step.value = 'scenario'
}

function goBack() {
  if (step.value === 'details') backToTemplateStep()
  else if (step.value === 'template' && needsScenarioStep.value) backToScenarioStep()
}

const breadcrumbItems = computed(() => [
  ...(needsScenarioStep.value && chosenScenario.value
    ? [{ label: chosenScenario.value.name, icon: 'i-lucide-layers', onClick: backToScenarioStep }]
    : []),
  { label: 'Choose template', onClick: backToTemplateStep },
  ...(step.value === 'details' && selectedTemplate.value
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
        predecessorContacts.value,
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
        <UBreadcrumb
          v-if="step === 'details' || (step === 'template' && needsScenarioStep)"
          :items="breadcrumbItems"
        />

        <div v-if="step === 'scenario'" class="flex flex-col gap-2">
          <p class="text-sm text-muted">
            Which scenario does this actual contact belong to? Only that scenario's contact
            templates and individuals are offered in the next steps.
          </p>
          <URadioGroup
            v-model="chosenScenarioId"
            :items="scenarioItems"
            variant="table"
            class="w-full"
          />
        </div>

        <div v-else-if="step === 'template'" class="flex flex-col gap-2">
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
            :scenario-id="chosenScenarioId"
          />
          <UFormField
            :label="individualSide === 'donor' ? 'Donors' : 'Recipients'"
            hint="One contact is created per selected individual"
          >
            <IndividualMultiSelect
              v-model="batchIndividualIds"
              :study-id="props.studyId"
              :scenario-id="chosenScenarioId"
            />
          </UFormField>
          <UAlert
            v-if="predecessorTemplate"
            color="info"
            variant="outline"
            icon="i-lucide-link"
            :description="`These contacts follow '${templateName(predecessorTemplate)}'. Each one is chained to the earlier contact of the same individual, if there is one.`"
          />
        </template>

        <template v-else-if="selectedTemplate">
          <SurfaceInstanceForm
            v-model="draft.donorSurface"
            :study-id="props.studyId"
            label="Donor"
            :template="selectedTemplate.donor_surface_template ?? null"
            :existing-surfaces="donorExistingSurfaces"
            :scenario-id="chosenScenarioId"
          />
          <SurfaceInstanceForm
            v-model="draft.recipientSurface"
            :study-id="props.studyId"
            label="Recipient"
            :template="selectedTemplate.recipient_surface_template ?? null"
            :existing-surfaces="recipientExistingSurfaces"
            :scenario-id="chosenScenarioId"
          />
          <UFormField v-if="predecessorTemplate" label="Follows contact" hint="Optional">
            <USelect
              :model-value="draft.previousContactId ?? NO_PREDECESSOR"
              :items="predecessorItems"
              class="w-full"
              @update:model-value="(value: string) => (draft.previousContactId = value === NO_PREDECESSOR ? null : value)"
            />
          </UFormField>
          <UFormField label="Name" hint="Optional - helps tell otherwise identical contacts apart">
            <UInput v-model="draft.name" class="w-full" />
          </UFormField>
        </template>

        <UAlert v-if="submitError" color="error" variant="outline" :description="submitError" />
      </div>
    </template>
    <template #footer>
      <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="visible = false" />
      <UButton
        v-if="step === 'details' || (step === 'template' && needsScenarioStep)"
        label="Back"
        icon="i-lucide-arrow-left"
        variant="ghost"
        @click="goBack"
      />
      <UButton
        v-if="step === 'scenario'"
        label="Continue"
        icon="i-lucide-arrow-right"
        trailing
        :disabled="!chosenScenarioId"
        @click="continueWithScenario"
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
