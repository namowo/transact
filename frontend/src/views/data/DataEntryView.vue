<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DataTable from 'openvue/datatable'
import Column from 'openvue/column'
import ContextMenu from 'openvue/contextmenu'
import { FilterMatchMode } from '@openvue/core/api'
import type { TabsItem } from '@nuxt/ui'
import type { MenuItem } from 'openvue/menuitem'
import ContactInstanceDialog from '@/components/data/ContactInstanceDialog.vue'
import IndividualsPanel from '@/components/data/IndividualsPanel.vue'
import ItemsPanel from '@/components/data/ItemsPanel.vue'
import RecoveriesPanel from '@/components/data/RecoveriesPanel.vue'
import ResultsTab from '@/components/scenarios/ResultsTab.vue'
import { templateName, surfaceInstanceIcon, surfaceInstanceDetail } from '@/components/data/contactTemplateLabel'
import { useIndividualOptions } from '@/components/scenarios/individualOptions'
import { useConfirm } from '@/composables/useConfirm'
import { listScenarios } from '@/api/scenarios'
import { listContacts, deleteContact, updateContact } from '@/api/contacts'
import type { Contact, ContactTemplate, Recovery } from '@/api/types'

const confirm = useConfirm()
const route = useRoute()
const router = useRouter()

const props = defineProps<{ studyId: string }>()

const studyId = computed(() => props.studyId)

const { describeIndividual, individualName } = useIndividualOptions(props.studyId)

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
const editingNames = ref(false)

// Expand every group when entering edit-names mode, so the inputs this
// mode adds to each group's member table are actually visible right away
// instead of requiring each group to be expanded by hand first.
watch(editingNames, (isEditing) => {
  if (!isEditing) return
  expandedContactRows.value = Object.fromEntries(contactGroups.value.map((group) => [group.key, true]))
})

function onContactSaved(newContacts: Contact[]) {
  contacts.value = [...contacts.value, ...newContacts]
}

function contactTemplateFor(contact: Contact): ContactTemplate | null {
  return contactTemplates.value.find((t) => t.id === contact.contact_template_id) ?? null
}

// Which surface slot ('donor_surface' | 'recipient_surface') holds the item,
// for contact templates shaped item-on-one-side/individual-on-the-other.
// Mirrors ContactInstanceDialog's batching rule: only applies when exactly
// one side is an item.
function itemSideOf(template: ContactTemplate): 'donor_surface' | 'recipient_surface' | null {
  const donorIsItem = !!template.donor_surface_template?.item_id
  const recipientIsItem = !!template.recipient_surface_template?.item_id
  if (donorIsItem && !recipientIsItem) return 'donor_surface'
  if (recipientIsItem && !donorIsItem) return 'recipient_surface'
  return null
}

interface ContactGroup {
  key: string
  template: ContactTemplate | null
  itemSide: 'donor_surface' | 'recipient_surface' | null
  itemSurfaceId: string | null
  members: Contact[]
}

// Contacts sharing the same template and the same item-side surface
// instance (i.e. the same batch-created item-to-many-individuals entry) are
// grouped into one expandable row, so the table doesn't repeat the item's
// details once per individual.
const contactGroups = computed<ContactGroup[]>(() => {
  const groups = new Map<string, ContactGroup>()
  for (const contact of contacts.value) {
    const template = contactTemplateFor(contact)
    const itemSide = template ? itemSideOf(template) : null
    const itemSurfaceId = itemSide ? contact[itemSide]?.id ?? null : null
    const key = itemSide
      ? `${contact.contact_template_id}::${itemSurfaceId}`
      : `single::${contact.id}`

    const existing = groups.get(key)
    if (existing) {
      existing.members.push(contact)
    } else {
      groups.set(key, {
        key,
        template,
        itemSide,
        itemSurfaceId,
        members: [contact],
      })
    }
  }
  return [...groups.values()]
})

// Icon + text for one side ('donor_surface' | 'recipient_surface') of a
// single contact, using the individual's position label when that side
// holds an individual rather than an item.
function sideDisplay(contact: Contact, side: 'donor_surface' | 'recipient_surface') {
  const surface = contact[side]
  const label = surface?.individual
    ? describeIndividual(surface.individual)
    : surfaceInstanceDetail(surface)
  return { icon: surfaceInstanceIcon(surface), label }
}

// Variants of sideDisplay for the expanded member table, which shows sex/age
// as separate badges next to the individual's name instead of baked into one
// string (describeIndividual's "Name (sex, age)") - they're already visible
// elsewhere on the row, no need to repeat them in prose form too.
function sideIcon(contact: Contact, side: 'donor_surface' | 'recipient_surface'): string | null {
  return surfaceInstanceIcon(contact[side])
}

function sideIndividual(contact: Contact, side: 'donor_surface' | 'recipient_surface') {
  return contact[side]?.individual ?? null
}

function sideIndividualLabel(contact: Contact, side: 'donor_surface' | 'recipient_surface'): string | null {
  const individual = sideIndividual(contact, side)
  return individual ? individualName(individual) : null
}

// Donor/Recipient column display for a group row: the fixed item side
// shows the item once; the individual side shows either the single
// individual (ungrouped contact) or a count badge (batch group).
function groupSideDisplay(group: ContactGroup, side: 'donor_surface' | 'recipient_surface') {
  const first = group.members[0]
  if (!first) return { icon: null, label: '—' }
  if (group.itemSide === side || group.members.length === 1) {
    return sideDisplay(first, side)
  }
  return { icon: 'i-lucide-users', label: `${group.members.length} individuals` }
}

// The individual behind a group member row, for the expansion table's
// separate Individual/Sex/Age columns - plain text crammed into one string
// ("Individual 2 (female, 26y)") is harder to scan than a name plus badges.
function memberIndividual(contact: Contact, itemSide: 'donor_surface' | 'recipient_surface' | null) {
  const side = itemSide === 'donor_surface' ? 'recipient_surface' : 'donor_surface'
  return contact[side]?.individual ?? null
}

async function deleteContacts(ids: string[]) {
  await Promise.all(ids.map((id) => deleteContact(id)))
  const removed = new Set(ids)
  contacts.value = contacts.value.filter((c) => !removed.has(c.id))
}

function confirmDeleteContact(contact: Contact) {
  confirm.require({
    message: 'Delete this contact? This cannot be undone.',
    header: 'Delete contact',
    rejectLabel: 'Cancel',
    acceptLabel: 'Delete',
    acceptColor: 'error',
    accept: () => deleteContacts([contact.id]),
  })
}

// -- Rename contact --

const renameDialogVisible = ref(false)
const renamingContact = ref<Contact | null>(null)
const renameValue = ref('')
const renaming = ref(false)

function openRenameDialog(contact: Contact) {
  renamingContact.value = contact
  renameValue.value = contact.name ?? ''
  renameDialogVisible.value = true
}

// Patches a contact's name on the existing object in place, rather than
// replacing `contacts.value` with a new array/objects - contactGroups
// rebuilds group.members from contacts.value on every change, so swapping
// in fresh object references on every rename made rows visibly reorder
// mid-edit (the table's row identity depends on these objects staying the
// same instance, not just the same id).
function patchContactName(id: string, name: string | null) {
  const contact = contacts.value.find((c) => c.id === id)
  if (contact) contact.name = name
}

// Unnamed contacts are numbered by their position across all of this
// study's contacts (not just within their group), so a given contact's
// number stays meaningful and doesn't shift just because a different group
// gets expanded or collapsed.
function contactFallbackName(contact: Contact): string {
  const position = contacts.value.findIndex((c) => c.id === contact.id)
  return `Contact ${position + 1}`
}

// Edit-names mode keeps every row's input mounted at once (so several
// contacts can be renamed in one pass without re-opening anything per row),
// bypassing PrimeVue's single-row cell-edit machinery entirely.
const pendingMemberNames = new Map<string, string>()

function onMemberNameInput(contact: Contact, value: string) {
  pendingMemberNames.set(contact.id, value)
}

async function onMemberNameBlur(contact: Contact) {
  const pending = pendingMemberNames.get(contact.id)
  pendingMemberNames.delete(contact.id)
  if (pending === undefined) return
  const trimmed = pending.trim() || null
  if (trimmed === (contact.name ?? null)) return
  await updateContact(contact.id, { name: trimmed })
  patchContactName(contact.id, trimmed)
}

async function saveRename() {
  if (!renamingContact.value) return
  renaming.value = true
  try {
    const name = renameValue.value.trim() || null
    await updateContact(renamingContact.value.id, { name })
    patchContactName(renamingContact.value.id, name)
    renameDialogVisible.value = false
  } finally {
    renaming.value = false
  }
}

// Inline cell edit on the expanded member table's Name column - a quicker
// path to the same rename than opening the dialog, for renaming several
// contacts in a row.
async function onMemberNameEditComplete(event: { data: Contact; newValue: string; field: string }) {
  const trimmed = event.newValue.trim() || null
  if (trimmed === (event.data.name ?? null)) return
  await updateContact(event.data.id, { name: trimmed })
  patchContactName(event.data.id, trimmed)
}

function confirmDeleteGroup(group: ContactGroup) {
  const count = group.members.length
  confirm.require({
    message:
      count > 1
        ? `Delete all ${count} contacts in this group? This cannot be undone.`
        : 'Delete this contact? This cannot be undone.',
    header: count > 1 ? `Delete ${count} contacts` : 'Delete contact',
    rejectLabel: 'Cancel',
    acceptLabel: 'Delete',
    acceptColor: 'error',
    accept: () => deleteContacts(group.members.map((c) => c.id)),
  })
}

// -- Context menu --

const contactContextMenu = ref<InstanceType<typeof ContextMenu>>()
const contextMenuGroup = ref<ContactGroup>()
const contextMenuContact = ref<Contact>()

const groupContextMenuItems = computed<MenuItem[]>(() => {
  const group = contextMenuGroup.value
  if (!group) return []
  const items: MenuItem[] = []
  if (group.members.length === 1) {
    items.push({
      label: 'Rename',
      icon: 'i-lucide-pencil',
      command: () => openRenameDialog(group.members[0]),
    })
  }
  items.push({
    label: group.members.length > 1 ? `Delete all ${group.members.length} contacts` : 'Delete',
    icon: 'i-lucide-trash-2',
    command: () => confirmDeleteGroup(group),
  })
  return items
})

const memberContextMenuItems = computed<MenuItem[]>(() => {
  const contact = contextMenuContact.value
  if (!contact) return []
  return [
    {
      label: 'Rename',
      icon: 'i-lucide-pencil',
      command: () => openRenameDialog(contact),
    },
    {
      label: 'Delete',
      icon: 'i-lucide-trash-2',
      command: () => confirmDeleteContact(contact),
    },
  ]
})

function openGroupContextMenu(event: Event, group: ContactGroup) {
  contextMenuContact.value = undefined
  contextMenuGroup.value = group
  contactContextMenu.value?.show(event)
}

function openMemberContextMenu(event: Event, contact: Contact) {
  contextMenuGroup.value = undefined
  contextMenuContact.value = contact
  contactContextMenu.value?.show(event)
}

function onGroupRowContextMenu(event: { originalEvent: Event; data: ContactGroup }) {
  openGroupContextMenu(event.originalEvent, event.data)
}

const expandedContactRows = ref<Record<string, boolean>>({})

function initContactFilters() {
  return {
    global: { value: null, matchMode: FilterMatchMode.CONTAINS },
  }
}

const contactFilters = ref(initContactFilters())

function clearContactFilters() {
  contactFilters.value = initContactFilters()
}

const tabItems = computed<TabsItem[]>(() => [
  { label: 'Individuals', value: 'individuals', slot: 'individuals' },
  { label: 'Items', value: 'items', slot: 'items' },
  { label: 'Contacts', value: 'contacts', slot: 'contacts', badge: contacts.value.length },
  { label: 'Recoveries', value: 'recoveries', slot: 'recoveries' },
  { label: 'Results', value: 'results', slot: 'results' },
])

const tabValues = new Set(['individuals', 'items', 'contacts', 'recoveries', 'results'])

const activeTab = computed<string>({
  get() {
    const tab = route.query.tab
    return typeof tab === 'string' && tabValues.has(tab) ? tab : 'individuals'
  },
  set(value) {
    router.replace({ query: { ...route.query, tab: value } })
  },
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <h1 class="text-2xl font-bold text-surface-900 dark:text-surface-0">Data entry</h1>

    <div v-if="loading" class="flex justify-center py-12">
      <UProgress class="w-12" />
    </div>

    <UAlert v-else-if="loadError" color="error" variant="outline" :description="loadError" />

    <UTabs v-else v-model="activeTab" :items="tabItems" class="w-full">
      <template #individuals>
        <IndividualsPanel :study-id="studyId" />
      </template>

      <template #items>
        <ItemsPanel :study-id="studyId" :contact-templates="contactTemplates" />
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
              variant="outline"
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
            <div class="mb-3 flex items-center justify-between gap-3">
              <div class="flex gap-2">
                <UButton
                  type="button"
                  icon="i-lucide-filter-x"
                  variant="outline"
                  size="sm"
                  @click="clearContactFilters()"
                >
                  Clear Filters
                </UButton>
                <UButton
                  type="button"
                  :label="editingNames ? 'Done' : 'Edit names'"
                  :icon="editingNames ? 'i-lucide-check' : 'i-lucide-pencil'"
                  :variant="editingNames ? 'solid' : 'outline'"
                  size="sm"
                  :disabled="!contacts.length"
                  @click="editingNames = !editingNames"
                />
              </div>
              <UInput
                v-model="contactFilters['global'].value"
                type="text"
                icon="i-lucide-search"
                placeholder="Keyword Search"
              />
            </div>

            <ContextMenu ref="contactContextMenu" :model="contextMenuGroup ? groupContextMenuItems : memberContextMenuItems" />

            <DataTable
              v-model:filters="contactFilters"
              v-model:expanded-rows="expandedContactRows"
              :value="contactGroups"
              data-key="key"
              filter-display="menu"
              :global-filter-fields="['template.name']"
              :row-class="() => 'hover:bg-elevated'"
              @row-contextmenu="onGroupRowContextMenu"
            >
              <template #empty>No actual contacts recorded yet.</template>
              <Column expander style="width: 2.5rem" />
              <Column header="Contact template">
                <template #body="{ data }">{{ data.template ? templateName(data.template) : '—' }}</template>
              </Column>
              <Column header="Donor">
                <template #body="{ data }">
                  <span class="flex items-center gap-1.5">
                    <UIcon v-if="groupSideDisplay(data, 'donor_surface').icon" :name="groupSideDisplay(data, 'donor_surface').icon!" class="shrink-0" />
                    {{ groupSideDisplay(data, 'donor_surface').label }}
                  </span>
                </template>
              </Column>
              <Column header="Recipient">
                <template #body="{ data }">
                  <span class="flex items-center gap-1.5">
                    <UIcon v-if="groupSideDisplay(data, 'recipient_surface').icon" :name="groupSideDisplay(data, 'recipient_surface').icon!" class="shrink-0" />
                    {{ groupSideDisplay(data, 'recipient_surface').label }}
                  </span>
                </template>
              </Column>
              <Column header="Contacts" style="width: 6rem">
                <template #body="{ data }">{{ data.members.length }}</template>
              </Column>
              <Column header="" style="width: 3rem">
                <template #body="{ data }">
                  <UButton
                    icon="i-lucide-more-vertical"
                    color="neutral"
                    variant="ghost"
                    square
                    aria-label="Contact options"
                    @click.stop="openGroupContextMenu($event, data)"
                  />
                </template>
              </Column>

              <template #expansion="{ data: group }">
                <DataTable
                  :value="group.members"
                  data-key="id"
                  edit-mode="cell"
                  :row-class="() => 'hover:bg-elevated'"
                  @row-contextmenu="(event: { originalEvent: Event; data: Contact }) => openMemberContextMenu(event.originalEvent, event.data)"
                  @cell-edit-complete="onMemberNameEditComplete"
                >
                  <Column header="Name" field="name">
                    <template #body="{ data }">
                      <UInput
                        v-if="editingNames"
                        :model-value="data.name"
                        :placeholder="contactFallbackName(data)"
                        class="w-full"
                        @update:model-value="(value: string) => onMemberNameInput(data, value)"
                        @blur="onMemberNameBlur(data)"
                        @keyup.enter="($event.target as HTMLElement)?.blur()"
                      />
                      <template v-else>{{ data.name || contactFallbackName(data) }}</template>
                    </template>
                    <template v-if="!editingNames" #editor="{ data, field }">
                      <UInput v-model="data[field]" autofocus class="w-full" @keyup.enter="($event.target as HTMLElement)?.blur()" />
                    </template>
                  </Column>
                  <Column header="Donor">
                    <template #body="{ data }">
                      <span class="flex items-center gap-1.5">
                        <UIcon v-if="sideIcon(data, 'donor_surface')" :name="sideIcon(data, 'donor_surface')!" class="shrink-0" />
                        {{ sideIndividualLabel(data, 'donor_surface') ?? sideDisplay(data, 'donor_surface').label }}
                        <UBadge v-if="sideIndividual(data, 'donor_surface')?.sex?.name" color="neutral" variant="outline">
                          {{ sideIndividual(data, 'donor_surface')!.sex!.name }}
                        </UBadge>
                        <UBadge v-if="sideIndividual(data, 'donor_surface')?.age != null" color="neutral" variant="outline">
                          {{ sideIndividual(data, 'donor_surface')!.age }}y
                        </UBadge>
                      </span>
                    </template>
                  </Column>
                  <Column header="Recipient">
                    <template #body="{ data }">
                      <span class="flex items-center gap-1.5">
                        <UIcon v-if="sideIcon(data, 'recipient_surface')" :name="sideIcon(data, 'recipient_surface')!" class="shrink-0" />
                        {{ sideIndividualLabel(data, 'recipient_surface') ?? sideDisplay(data, 'recipient_surface').label }}
                        <UBadge v-if="sideIndividual(data, 'recipient_surface')?.sex?.name" color="neutral" variant="outline">
                          {{ sideIndividual(data, 'recipient_surface')!.sex!.name }}
                        </UBadge>
                        <UBadge v-if="sideIndividual(data, 'recipient_surface')?.age != null" color="neutral" variant="outline">
                          {{ sideIndividual(data, 'recipient_surface')!.age }}y
                        </UBadge>
                      </span>
                    </template>
                  </Column>
                  <Column header="" style="width: 3rem">
                    <template #body="{ data }">
                      <UButton
                        icon="i-lucide-more-vertical"
                        color="neutral"
                        variant="ghost"
                        square
                        aria-label="Contact options"
                        @click.stop="openMemberContextMenu($event, data)"
                      />
                    </template>
                  </Column>
                </DataTable>
              </template>
            </DataTable>
          </div>

          <ContactInstanceDialog
            v-model:visible="dialogVisible"
            :study-id="studyId"
            :contact-templates="contactTemplates"
            :contacts="contacts"
            @saved="onContactSaved"
          />

          <UModal
            v-model:open="renameDialogVisible"
            title="Rename contact"
            :ui="{ content: 'max-w-sm', footer: 'justify-end' }"
          >
            <template #body>
              <UFormField label="Name" hint="Optional - helps tell otherwise identical contacts apart">
                <UInput v-model="renameValue" class="w-full" @keyup.enter="saveRename" />
              </UFormField>
            </template>
            <template #footer>
              <UButton label="Cancel" icon="i-lucide-x" variant="ghost" @click="renameDialogVisible = false" />
              <UButton label="Save" icon="i-lucide-save" :loading="renaming" @click="saveRename" />
            </template>
          </UModal>
        </div>
      </template>

      <template #recoveries>
        <RecoveriesPanel
          :study-id="studyId"
          :contacts="contacts"
          :contact-templates="contactTemplates"
          @update:recoveries="scopedRecoveries = $event"
        />
      </template>

      <template #results>
        <ResultsTab :recoveries="scopedRecoveries" :study-id="studyId" />
      </template>
    </UTabs>
  </div>
</template>
