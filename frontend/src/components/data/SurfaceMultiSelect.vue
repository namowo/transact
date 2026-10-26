<script setup lang="ts">
import { computed, ref } from 'vue'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import { FilterMatchMode } from '@openvue/core/api'
import { templateName, surfaceInstanceIcon, surfaceInstanceDetail } from './contactTemplateLabel'
import { useIndividualOptions } from '@/components/scenarios/individualOptions'
import type { Contact, ContactTemplate, Surface } from '@/api/types'

// Lets the user pick several surfaces at once when recording recoveries, one
// checkbox for the donor surface and one for the recipient surface per
// actual contact - mirroring the Contacts tab's own table, just with the
// row's two surfaces made selectable instead of merely displayed.
const props = defineProps<{
  studyId: string
  contacts: Contact[]
  contactTemplates: ContactTemplate[]
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
  return surface.individual ? describeIndividual(surface.individual) : surfaceInstanceDetail(surface)
}

interface ContactRow {
  contact: Contact
  contactLabel: string
  donorLabel: string
  recipientLabel: string
}

// Flattened, human-readable text per row so the table's filter searches what
// the user actually sees, not raw Contact/Surface objects.
const rows = computed<ContactRow[]>(() =>
  props.contacts.map((contact) => ({
    contact,
    contactLabel: contactLabel(contact),
    donorLabel: surfaceDetail(contact.donor_surface),
    recipientLabel: surfaceDetail(contact.recipient_surface),
  })),
)

function isSelected(surface?: Surface | null): boolean {
  return !!surface && surfaceIds.value.includes(surface.id)
}

function toggleSurface(surface?: Surface | null) {
  if (!surface) return
  const next = new Set(surfaceIds.value)
  if (next.has(surface.id)) next.delete(surface.id)
  else next.add(surface.id)
  surfaceIds.value = [...next]
}

function initFilters() {
  return {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
  }
}

const filters = ref(initFilters())

function clearFilters() {
  filters.value = initFilters()
}
</script>

<template>
  <div class="flex flex-col gap-2">
    <div class="flex items-center justify-between gap-3">
      <UButton type="button" icon="i-lucide-filter-x" variant="outline" size="sm" @click="clearFilters()">
        Clear Filters
      </UButton>
      <UInput
        v-model="(filters['global'] as { value: string | null }).value"
        type="text"
        icon="i-lucide-search"
        placeholder="Keyword Search"
      />
    </div>
    <div class="border border-default rounded-md overflow-hidden">
      <DataTable
        v-model:filters="filters"
        :value="rows"
        data-key="contact.id"
        filter-display="menu"
        :global-filter-fields="['contactLabel', 'donorLabel', 'recipientLabel']"
        scrollable
        scroll-height="18rem"
      >
        <template #empty>No surfaces yet. Add an actual contact first.</template>
        <Column field="contactLabel" header="Contact" sortable>
          <template #body="{ data }">{{ data.contactLabel }}</template>
        </Column>
        <Column header="Donor">
          <template #body="{ data }">
            <label class="flex items-center gap-2 cursor-pointer">
              <UCheckbox
                :model-value="isSelected(data.contact.donor_surface)"
                :disabled="!data.contact.donor_surface"
                @update:model-value="toggleSurface(data.contact.donor_surface)"
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
        </Column>
        <Column header="Recipient">
          <template #body="{ data }">
            <label class="flex items-center gap-2 cursor-pointer">
              <UCheckbox
                :model-value="isSelected(data.contact.recipient_surface)"
                :disabled="!data.contact.recipient_surface"
                @update:model-value="toggleSurface(data.contact.recipient_surface)"
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
        </Column>
      </DataTable>
    </div>
  </div>
</template>
