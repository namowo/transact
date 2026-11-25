<script setup lang="ts">
import { computed, ref } from 'vue'
import { templateName, surfaceInstanceIcon, surfaceInstanceDetail } from './contactTemplateLabel'
import { useIndividualOptions } from '@/components/scenarios/individualOptions'
import ScenarioBadges from './ScenarioBadges.vue'
import type { Contact, ContactTemplate, Scenario, Surface } from '@/api/types'
import type { TableColumn } from '@nuxt/ui'
import { manualSorting, useTableView } from '@/composables/useTableView'
import { sortHeader } from '@/composables/tableColumns'
import TableFilterDrawer from '@/components/ui/TableFilterDrawer.vue'

// Lets the user pick several surfaces at once when recording samples, one
// checkbox for the donor surface and one for the recipient surface per
// actual contact - mirroring the Contacts tab's own table, just with the
// row's two surfaces made selectable instead of merely displayed.
const props = defineProps<{
  studyId: string
  contacts: Contact[]
  contactTemplates: ContactTemplate[]
  scenarios: Scenario[]
}>()

const surfaceIds = defineModel<string[]>({ default: () => [] })

const { describeIndividual } = useIndividualOptions(props.studyId)

function contactTemplateFor(contact: Contact): ContactTemplate | null {
  return props.contactTemplates.find((t) => t.id === contact.contact_template_id) ?? null
}

function contactLabel(contact: Contact): string {
  const template = contactTemplateFor(contact)
  return template ? templateName(template) : `Contact #${contact.id.slice(0, 8)}`
}

function surfaceDetail(surface?: Surface | null): string {
  if (!surface) return '—'
  return surface.individual
    ? describeIndividual(surface.individual)
    : surfaceInstanceDetail(surface)
}

// Narrow the contacts to one scenario (via the contact's template).
const scenarioFilter = ref('all')

const scenarioOptions = computed(() => [
  { label: 'All scenarios', value: 'all' },
  ...props.scenarios.map((scenario) => ({ label: scenario.name, value: scenario.id })),
])

function scenarioNamesOf(contact: Contact): string[] {
  return props.scenarios
    .filter((s) => s.contact_templates.some((t) => t.id === contact.contact_template_id))
    .map((s) => s.name)
}

const scopedContacts = computed(() => {
  if (scenarioFilter.value === 'all') return props.contacts
  const scenario = props.scenarios.find((s) => s.id === scenarioFilter.value)
  const templateIds = new Set((scenario?.contact_templates ?? []).map((t) => t.id))
  return props.contacts.filter((c) => templateIds.has(c.contact_template_id ?? ''))
})

interface ContactRow {
  contact: Contact
  contactLabel: string
  scenarioNames: string
  donorLabel: string
  recipientLabel: string
}

// Flattened, human-readable text per row so the table's filter searches what
// the user actually sees, not raw Contact/Surface objects.
const rows = computed<ContactRow[]>(() =>
  scopedContacts.value.map((contact) => ({
    contact,
    contactLabel: contactLabel(contact),
    scenarioNames: scenarioNamesOf(contact).join(', '),
    donorLabel: surfaceDetail(contact.donor_surface),
    recipientLabel: surfaceDetail(contact.recipient_surface),
  })),
)

type Side = 'donor_surface' | 'recipient_surface'

// A selection is one side of one contact ("<contact id>|<side>"), not a bare
// surface: a batch of contacts shares a single item surface, and each of
// those contacts still needs its own sample.
const selectionKey = (contact: Contact, side: Side) => `${contact.id}|${side}`

function isSelected(contact: Contact, side: Side): boolean {
  return !!contact[side] && surfaceIds.value.includes(selectionKey(contact, side))
}

function toggleSurface(contact: Contact, side: Side) {
  if (!contact[side]) return
  const key = selectionKey(contact, side)
  const next = new Set(surfaceIds.value)
  if (next.has(key)) next.delete(key)
  else next.add(key)
  surfaceIds.value = [...next]
}

// Contacts that have a surface on one side, for the header's select-all.
function sideContacts(side: Side): Contact[] {
  return scopedContacts.value.filter((contact) => !!contact[side])
}

function sideState(side: Side): boolean | 'indeterminate' {
  const contacts = sideContacts(side)
  const selected = contacts.filter((contact) => isSelected(contact, side)).length
  if (!selected) return false
  return selected === contacts.length ? true : 'indeterminate'
}

function toggleSide(side: Side) {
  const keys = sideContacts(side).map((contact) => selectionKey(contact, side))
  const next = new Set(surfaceIds.value)
  if (sideState(side) === true) keys.forEach((key) => next.delete(key))
  else keys.forEach((key) => next.add(key))
  surfaceIds.value = [...next]
}

const view = useTableView(rows, {
  searchFields: ['contactLabel', 'scenarioNames', 'donorLabel', 'recipientLabel'],
})

const columns: TableColumn<ContactRow>[] = [
  { id: 'contactLabel', accessorKey: 'contactLabel', header: sortHeader('Contact') },
  { id: 'scenario', header: 'Scenario' },
  { id: 'donor', header: 'Donor' },
  { id: 'recipient', header: 'Recipient' },
]
</script>

<template>
  <div class="flex flex-col gap-2">
    <div class="flex items-center justify-between gap-3">
      <UInput
        v-model="view.search"
        icon="i-lucide-search"
        placeholder="Keyword Search"
        class="w-full max-w-sm"
      />
      <TableFilterDrawer
        :active-count="scenarioFilter === 'all' ? 0 : 1"
        @reset="scenarioFilter = 'all'"
      >
        <UFormField label="Scenario">
          <USelect v-model="scenarioFilter" :items="scenarioOptions" class="w-full" />
        </UFormField>
      </TableFilterDrawer>
    </div>
    <div class="border border-default rounded-md overflow-hidden">
      <UTable
        v-model:sorting="view.sorting"
        :sorting-options="manualSorting"
        :data="view.rows"
        :columns="columns"
        :get-row-id="(row: ContactRow) => row.contact.id"
        empty="No surfaces yet. Add an actual contact first."
        sticky
        class="max-h-72"
      >
        <template #scenario-cell="{ row }"
          ><ScenarioBadges :names="scenarioNamesOf(row.original.contact)"
        /></template>
        <template #donor-header>
          <label class="flex items-center gap-2 cursor-pointer">
            <UCheckbox
              :model-value="sideState('donor_surface')"
              :disabled="!sideContacts('donor_surface').length"
              @update:model-value="toggleSide('donor_surface')"
            />
            <span class="font-semibold">Donor</span>
          </label>
        </template>
        <template #donor-cell="{ row: { original: data } }">
          <label class="flex items-center gap-2 cursor-pointer">
            <UCheckbox
              :model-value="isSelected(data.contact, 'donor_surface')"
              :disabled="!data.contact.donor_surface"
              @update:model-value="toggleSurface(data.contact, 'donor_surface')"
            />
            <span class="flex items-center gap-1.5">
              <UIcon
                v-if="surfaceInstanceIcon(data.contact.donor_surface)"
                :name="surfaceInstanceIcon(data.contact.donor_surface)!"
                class="shrink-0"
              />
              {{ data.donorLabel }}
            </span>
          </label>
        </template>
        <template #recipient-header>
          <label class="flex items-center gap-2 cursor-pointer">
            <UCheckbox
              :model-value="sideState('recipient_surface')"
              :disabled="!sideContacts('recipient_surface').length"
              @update:model-value="toggleSide('recipient_surface')"
            />
            <span class="font-semibold">Recipient</span>
          </label>
        </template>
        <template #recipient-cell="{ row: { original: data } }">
          <label class="flex items-center gap-2 cursor-pointer">
            <UCheckbox
              :model-value="isSelected(data.contact, 'recipient_surface')"
              :disabled="!data.contact.recipient_surface"
              @update:model-value="toggleSurface(data.contact, 'recipient_surface')"
            />
            <span class="flex items-center gap-1.5">
              <UIcon
                v-if="surfaceInstanceIcon(data.contact.recipient_surface)"
                :name="surfaceInstanceIcon(data.contact.recipient_surface)!"
                class="shrink-0"
              />
              {{ data.recipientLabel }}
            </span>
          </label>
        </template>
      </UTable>
    </div>
  </div>
</template>
