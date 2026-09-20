<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import type { TabsItem } from '@nuxt/ui'
import ContactInstanceDialog from '@/components/data/ContactInstanceDialog.vue'
import IndividualsAndItemsPanel from '@/components/data/IndividualsAndItemsPanel.vue'
import RecoveriesPanel from '@/components/data/RecoveriesPanel.vue'
import ResultsTab from '@/components/scenarios/ResultsTab.vue'
import { listScenarios } from '@/api/scenarios'
import { listContacts, deleteContact } from '@/api/contacts'
import type { Contact, ContactTemplate, Recovery } from '@/api/types'

const props = defineProps<{ studyId: string }>()

const studyId = computed(() => props.studyId)

const loading = ref(false)
const loadError = ref('')

const contactTemplates = ref<ContactTemplate[]>([])
const contacts = ref<Contact[]>([])
const scopedRecoveries = ref<Recovery[]>([])

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const allScenarios = await listScenarios()
    const studyScenarios = allScenarios.filter((scenario) =>
      scenario.studies.some((study) => study.id === studyId.value),
    )
    const templates = studyScenarios.flatMap((scenario) => scenario.contact_templates)
    contactTemplates.value = templates

    const templateIds = new Set(templates.map((t) => t.id))
    const allContacts = await listContacts()
    contacts.value = allContacts.filter(
      (contact) => contact.contact_template_id != null && templateIds.has(contact.contact_template_id),
    )
  } catch {
    loadError.value = 'Could not load data for this study.'
  } finally {
    loading.value = false
  }
}

onMounted(load)

const dialogVisible = ref(false)

function onContactSaved(contact: Contact) {
  contacts.value = [...contacts.value, contact]
}

async function onDeleteContact(contact: Contact) {
  if (!window.confirm('Delete this contact? This cannot be undone.')) return
  await deleteContact(contact.id)
  contacts.value = contacts.value.filter((c) => c.id !== contact.id)
}

function surfaceSummary(contact: Contact, side: 'donor_surface' | 'recipient_surface'): string {
  const surface = contact[side]
  if (!surface) return '—'
  if (surface.individual) return 'Individual'
  const category = surface.surface_template?.item?.item_category?.name
  return category ? `Item (${category})` : 'Item'
}

const tabItems = computed<TabsItem[]>(() => [
  { label: 'Individuals & items', value: 'individuals-items', slot: 'individuals-items' },
  { label: 'Contacts', value: 'contacts', slot: 'contacts', badge: contacts.value.length },
  { label: 'Recoveries', value: 'recoveries', slot: 'recoveries' },
  { label: 'Results', value: 'results', slot: 'results' },
])
</script>

<template>
  <div class="flex flex-col gap-6">
    <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Data entry</h1>

    <div v-if="loading" class="flex justify-center py-12">
      <UProgress class="w-12" />
    </div>

    <UAlert v-else-if="loadError" color="error" variant="outline" :description="loadError" />

    <UTabs v-else default-value="contacts" :items="tabItems" class="w-full">
      <template #individuals-items>
        <IndividualsAndItemsPanel />
      </template>

      <template #contacts>
        <div class="flex flex-col gap-4">
          <div class="flex items-center justify-between">
            <p class="text-sm text-surface-500 dark:text-surface-400">
              Actual contacts recorded for this study's planned scenarios.
            </p>
            <UButton
              label="Add actual contact"
              icon="i-lucide-plus"
              :disabled="!contactTemplates.length"
              @click="dialogVisible = true"
            />
          </div>

          <UAlert
            v-if="!contactTemplates.length"
            color="info"
            variant="outline"
            description="Plan a scenario with at least one contact template before entering actual data."
          />

          <div class="overflow-x-auto">
            <DataTable :value="contacts" data-key="id">
              <Column header="Contact template">
                <template #body="{ data }">#{{ data.contact_template_id }}</template>
              </Column>
              <Column header="Donor">
                <template #body="{ data }">{{ surfaceSummary(data, 'donor_surface') }}</template>
              </Column>
              <Column header="Recipient">
                <template #body="{ data }">{{ surfaceSummary(data, 'recipient_surface') }}</template>
              </Column>
              <Column header="" style="width: 4rem">
                <template #body="{ data }">
                  <UButton
                    icon="i-lucide-trash-2"
                    variant="ghost"
                    square
                    color="error"
                    aria-label="Delete"
                    @click="onDeleteContact(data)"
                  />
                </template>
              </Column>
            </DataTable>
          </div>

          <ContactInstanceDialog
            v-model:visible="dialogVisible"
            :contact-templates="contactTemplates"
            @saved="onContactSaved"
          />
        </div>
      </template>

      <template #recoveries>
        <RecoveriesPanel
          :study-id="studyId"
          :contacts="contacts"
          @update:recoveries="scopedRecoveries = $event"
        />
      </template>

      <template #results>
        <ResultsTab :recoveries="scopedRecoveries" />
      </template>
    </UTabs>
  </div>
</template>
