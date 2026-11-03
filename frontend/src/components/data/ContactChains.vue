<script setup lang="ts">
import { computed, provide, ref } from 'vue'
import ContactChainNodeView from './ContactChainNode.vue'
import { contactChainDndKey } from './contactChain'
import { buildContactChains, chainLength } from './contactChain'
import { templateName } from './contactTemplateLabel'
import type { ContactChainInfo } from './ContactChainNode.vue'
import type { Contact, ContactTemplate } from '@/api/types'

const props = defineProps<{
  contacts: Contact[]
  contactTemplates: ContactTemplate[]
  info: (contact: Contact) => ContactChainInfo
  canUndo?: boolean
}>()

export interface LinkOp {
  contactId: string
  previousId: string | null
}

// A change is a list of link operations, applied in order.
const emit = defineEmits<{ change: [ops: LinkOp[]]; undo: [] }>()

const chains = computed(() => buildContactChains(props.contacts))

// Planned chains: templates linked through previous_contact_template_id,
// shown as ordered sequences (A, B, C) so the intended order is visible even
// before any actual contact has been recorded.
const plannedChains = computed(() => {
  const byId = new Map(props.contactTemplates.map((t) => [t.id, t]))
  const successorOf = new Map<string, ContactTemplate>()
  for (const template of props.contactTemplates) {
    if (template.previous_contact_template_id && byId.has(template.previous_contact_template_id)) {
      successorOf.set(template.previous_contact_template_id, template)
    }
  }
  return props.contactTemplates
    .filter((t) => !(t.previous_contact_template_id && byId.has(t.previous_contact_template_id)))
    .map((root) => {
      const sequence = [root]
      for (let next = successorOf.get(root.id); next && !sequence.includes(next); next = successorOf.get(next.id)) {
        sequence.push(next)
      }
      return sequence
    })
    .filter((sequence) => sequence.length > 1)
})

// The board only lists contacts that are not in a chain yet; chained ones
// live in "Recorded chains" below, which is also a drop target.
const contactsByTemplate = computed(() => {
  const map = new Map<string, Contact[]>()
  for (const contact of props.contacts) {
    if (!contact.contact_template_id) continue
    if (contact.previous_contact_id || followedIds.value.has(contact.id)) continue
    const list = map.get(contact.contact_template_id) ?? []
    list.push(contact)
    map.set(contact.contact_template_id, list)
  }
  return map
})

const contactById = computed(() => new Map(props.contacts.map((c) => [c.id, c])))

// -- Drag and drop: drop a contact onto a contact of the previous template --

const dragged = ref<Contact | null>(null)
const hoverTarget = ref<string | null>(null)
const highlighted = ref<string | null>(null)

// Which contact ends up first/second when `source` is dropped on `target`:
// null when their templates are not directly consecutive in either order.
// Each contact can be followed by only one other contact.
const followedIds = computed(
  () => new Set(props.contacts.map((c) => c.previous_contact_id).filter((id): id is string => !!id)),
)

function linkFor(source: Contact | null, target: Contact): { contactId: string; previousId: string } | null {
  const link = rawLinkFor(source, target)
  if (!link) return null
  return followedIds.value.has(link.previousId) ? null : link
}

function rawLinkFor(source: Contact | null, target: Contact): { contactId: string; previousId: string } | null {
  if (!source || source.id === target.id) return null
  const templateOf = (c: Contact) => props.contactTemplates.find((t) => t.id === c.contact_template_id)
  if (templateOf(source)?.previous_contact_template_id === target.contact_template_id) {
    return { contactId: source.id, previousId: target.id }
  }
  if (templateOf(target)?.previous_contact_template_id === source.contact_template_id) {
    return { contactId: target.id, previousId: source.id }
  }
  return null
}

// Dropping onto a contact of the same step swaps them: the dragged contact
// takes over the target's place in its chain (both the link to the contact
// before and the one to the contact after), and the target is unlinked.
function replaceFor(source: Contact | null, target: Contact): LinkOp[] | null {
  if (!source || source.id === target.id) return null
  if (source.contact_template_id !== target.contact_template_id) return null
  if (followedIds.value.has(source.id)) return null
  const follower = props.contacts.find((c) => c.previous_contact_id === target.id)
  if (!target.previous_contact_id && !follower) return null
  const ops: LinkOp[] = []
  if (target.previous_contact_id) ops.push({ contactId: target.id, previousId: null })
  ops.push({ contactId: source.id, previousId: target.previous_contact_id ?? null })
  if (follower) ops.push({ contactId: follower.id, previousId: source.id })
  return ops
}

function opsFor(source: Contact | null, target: Contact): LinkOp[] | null {
  const link = linkFor(source, target)
  return link ? [link] : replaceFor(source, target)
}

function canDropOn(target: Contact): boolean {
  return !!opsFor(dragged.value, target)
}

function onDragStart(event: DragEvent, contact: Contact) {
  dragged.value = contact
  event.dataTransfer?.setData('text/plain', contact.id)
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'link'
}

function onDragEnd() {
  dragged.value = null
  hoverTarget.value = null
}

function onDragOver(event: DragEvent, target: Contact) {
  if (!canDropOn(target)) return
  event.preventDefault()
  hoverTarget.value = target.id
}

function onDrop(target: Contact) {
  const ops = opsFor(dragged.value, target)
  if (ops) emit('change', ops)
  onDragEnd()
}

// Shared with the recursive chain diagram, so its nodes drag and drop
// exactly like the cards on the board.
provide(contactChainDndKey, {
  dragged,
  hoverTarget,
  canDropOn,
  onDragStart,
  onDragEnd,
  onDragOver,
  onDrop,
  unlink: (contact: Contact) => emit('change', [{ contactId: contact.id, previousId: null }]),
})

function isRelated(contact: Contact): boolean {
  const id = highlighted.value
  if (!id) return false
  const other = contactById.value.get(id)
  return contact.id === id || contact.previous_contact_id === id || other?.previous_contact_id === contact.id
}

function previousTitle(contact: Contact): string | null {
  const previous = contact.previous_contact_id ? contactById.value.get(contact.previous_contact_id) : null
  return previous ? props.info(previous).title : null
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex flex-col gap-3">
      <div class="flex items-start justify-between gap-3">
        <div>
          <h3 class="font-medium text-sm">Link contacts</h3>
          <p class="text-xs text-muted">
          Drag a contact onto a contact of the neighbouring step to chain it, in either direction. Chained contacts move to "Recorded chains" below, where you can also drop contacts onto them, swap them (drop onto a contact of the same step) or remove a link with the x.
          </p>
        </div>
        <UButton
          label="Undo"
          icon="i-lucide-undo-2"
          variant="outline"
          size="sm"
          :disabled="!canUndo"
          @click="emit('undo')"
        />
      </div>
      <UAlert
        v-if="!plannedChains.length"
        color="info"
        variant="outline"
        description="Chain contact templates in the scenario (Contact chain) to link their contacts here."
      />
      <div
        v-for="sequence in plannedChains"
        :key="sequence[0]!.id"
        class="overflow-x-auto"
      >
        <div class="flex items-start gap-2">
          <template v-for="(template, index) in sequence" :key="template.id">
            <UIcon v-if="index > 0" name="i-lucide-arrow-right" class="shrink-0 mt-2 text-dimmed" />
            <div class="w-64 shrink-0 rounded-md border border-default flex flex-col">
              <div class="px-3 py-2 border-b border-default flex items-center justify-between gap-2">
                <span class="font-medium text-sm truncate">{{ templateName(template) }}</span>
                <UBadge color="neutral" variant="subtle" :label="String(contactsByTemplate.get(template.id)?.length ?? 0)" />
              </div>
              <div class="flex flex-col gap-2 p-2 max-h-96 overflow-y-auto">
                <p v-if="!contactsByTemplate.get(template.id)?.length" class="text-xs text-muted p-1">
                  No unchained contacts.
                </p>
                <div
                  v-for="contact in contactsByTemplate.get(template.id) ?? []"
                  :key="contact.id"
                  draggable="true"
                  :class="[
                    'rounded-md border p-2 text-xs flex flex-col gap-0.5 select-none transition-colors',
                    'cursor-grab',
                    hoverTarget === contact.id
                      ? 'border-primary bg-primary/10'
                      : dragged && canDropOn(contact)
                        ? 'border-primary border-dashed'
                        : isRelated(contact)
                          ? 'border-primary bg-elevated'
                          : 'border-default',
                    dragged && dragged.id === contact.id ? 'opacity-40' : '',
                    dragged && !canDropOn(contact) && dragged.id !== contact.id ? 'opacity-50' : '',
                  ]"
                  @dragstart="onDragStart($event, contact)"
                  @dragend="onDragEnd"
                  @dragover="onDragOver($event, contact)"
                  @dragleave="hoverTarget = null"
                  @drop.prevent="onDrop(contact)"
                  @mouseenter="highlighted = contact.id"
                  @mouseleave="highlighted = null"
                >
                  <span class="font-medium truncate">{{ info(contact).title }}</span>
                  <span class="flex items-center gap-1 truncate text-muted">
                    <UIcon v-if="info(contact).donor.icon" :name="info(contact).donor.icon!" class="shrink-0" />
                    {{ info(contact).donor.label }}
                    <UIcon name="i-lucide-arrow-right" class="shrink-0" />
                    <UIcon v-if="info(contact).recipient.icon" :name="info(contact).recipient.icon!" class="shrink-0" />
                    {{ info(contact).recipient.label }}
                  </span>
                  <span v-if="followedIds.has(contact.id)" class="flex items-center gap-1 text-muted">
                    <UIcon name="i-lucide-corner-down-right" class="shrink-0" />
                    Already followed
                  </span>
                  <span v-if="index > 0" class="flex items-center justify-between gap-1">
                    <span v-if="previousTitle(contact)" class="flex items-center gap-1 text-primary truncate">
                      <UIcon name="i-lucide-corner-up-left" class="shrink-0" />
                      {{ previousTitle(contact) }}
                    </span>
                    <span v-else class="text-dimmed">Not linked</span>
                    <UButton
                      v-if="contact.previous_contact_id"
                      icon="i-lucide-x"
                      color="neutral"
                      variant="ghost"
                      size="xs"
                      square
                      aria-label="Unlink"
                      @click.stop="emit('change', [{ contactId: contact.id, previousId: null }])"
                    />
                  </span>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <div class="flex flex-col gap-2">
      <h3 class="font-medium text-sm">Recorded chains ({{ chains.length }})</h3>
      <UAlert
        v-if="!chains.length"
        color="info"
        variant="outline"
        description="No contacts are linked yet. Drag contacts onto each other above to chain them."
      />
      <div
        v-for="chain in chains"
        :key="chain.contact.id"
        class="overflow-x-auto rounded-md border border-default p-3"
      >
        <p class="text-xs text-muted mb-2">{{ chainLength(chain) }} contacts</p>
        <ContactChainNodeView :node="chain" :info="info" first />
      </div>
    </div>
  </div>
</template>
