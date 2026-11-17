import type { InjectionKey, Ref } from 'vue'
import type { Contact, ContactTemplate } from '@/api/types'

export interface ContactChainNode {
  contact: Contact
  next: ContactChainNode[]
}

// Builds the forest of chains from the contacts' previous_contact_id links.
// Roots are contacts with no (known) predecessor; contacts whose predecessor
// is outside the given list count as roots too, so a filtered view never
// drops them. Only roots that actually lead somewhere are returned unless
// includeSingles is set.
export function buildContactChains(
  contacts: Contact[],
  includeSingles = false,
): ContactChainNode[] {
  const nodes = new Map<string, ContactChainNode>(
    contacts.map((contact) => [contact.id, { contact, next: [] }]),
  )
  const roots: ContactChainNode[] = []
  for (const node of nodes.values()) {
    const parent = node.contact.previous_contact_id
      ? nodes.get(node.contact.previous_contact_id)
      : undefined
    if (parent) parent.next.push(node)
    else roots.push(node)
  }
  return includeSingles ? roots : roots.filter((root) => root.next.length > 0)
}

export function chainLength(node: ContactChainNode): number {
  return 1 + node.next.reduce((sum, child) => sum + chainLength(child), 0)
}

// The individual taking part in a contact, whichever side they are on.
export function contactIndividualIds(contact: Contact): string[] {
  return [contact.donor_surface?.individual_id, contact.recipient_surface?.individual_id].filter(
    (id): id is string => !!id,
  )
}

export interface ContactChainDnd {
  dragged: Ref<Contact | null>
  hoverTarget: Ref<string | null>
  canDropOn: (target: Contact) => boolean
  onDragStart: (event: DragEvent, contact: Contact) => void
  onDragEnd: () => void
  onDragOver: (event: DragEvent, target: Contact) => void
  onDrop: (target: Contact) => void
  unlink: (contact: Contact) => void
}

export const contactChainDndKey: InjectionKey<ContactChainDnd> = Symbol('contactChainDnd')

// Contact templates grouped into their planned order, following
// previous_contact_template_id: every chain of templates becomes one
// sequence (A, B, C). Templates that are not chained to anything form a
// sequence of their own, so every template appears exactly once.
export function plannedTemplateSequences(templates: ContactTemplate[]): ContactTemplate[][] {
  const byId = new Map(templates.map((t) => [t.id, t]))
  const successorOf = new Map<string, ContactTemplate>()
  for (const template of templates) {
    const previousId = template.previous_contact_template_id
    if (previousId && byId.has(previousId) && !successorOf.has(previousId)) {
      successorOf.set(previousId, template)
    }
  }
  const placed = new Set<string>()
  const sequences: ContactTemplate[][] = []
  const startSequence = (root: ContactTemplate) => {
    const sequence = [root]
    placed.add(root.id)
    for (let next = successorOf.get(root.id); next && !placed.has(next.id); next = successorOf.get(next.id)) {
      sequence.push(next)
      placed.add(next.id)
    }
    sequences.push(sequence)
  }
  for (const template of templates) {
    const previousId = template.previous_contact_template_id
    if (!(previousId && byId.has(previousId))) startSequence(template)
  }
  // Anything left over sits in a cycle; start it anywhere rather than drop it.
  for (const template of templates) if (!placed.has(template.id)) startSequence(template)
  return sequences
}

// Ids of everything a contact touches - individuals and the surfaces
// themselves - used to recognise that two contacts belong in one chain.
function contactParticipants(contact: Contact): Set<string> {
  const ids = new Set<string>(contactIndividualIds(contact).map((id) => `individual:${id}`))
  for (const surface of [contact.donor_surface, contact.recipient_surface]) {
    if (surface?.id) ids.add(`surface:${surface.id}`)
  }
  return ids
}

// Proposes links for contacts that are not chained yet: a contact of a
// template that follows another template is linked to a contact of that
// earlier template sharing an individual or a surface with it. Individuals
// may occur any number of times in a chain; each contact can only be
// followed by one other contact. When `onlyIds` is given, only links that
// involve at least one of those contacts are proposed.
export function autoLinkOps(
  contacts: Contact[],
  templates: ContactTemplate[],
  onlyIds?: Set<string>,
): { contactId: string; previousId: string }[] {
  const templateById = new Map(templates.map((t) => [t.id, t]))
  const followed = new Set(contacts.map((c) => c.previous_contact_id).filter((id): id is string => !!id))
  const ops: { contactId: string; previousId: string }[] = []
  for (const contact of contacts) {
    if (contact.previous_contact_id) continue
    const previousTemplateId = templateById.get(contact.contact_template_id ?? '')?.previous_contact_template_id
    if (!previousTemplateId) continue
    const own = contactParticipants(contact)
    const predecessor = contacts.find(
      (candidate) =>
        candidate.id !== contact.id &&
        candidate.contact_template_id === previousTemplateId &&
        !followed.has(candidate.id) &&
        (!onlyIds || onlyIds.has(contact.id) || onlyIds.has(candidate.id)) &&
        [...contactParticipants(candidate)].some((id) => own.has(id)),
    )
    if (!predecessor) continue
    followed.add(predecessor.id)
    ops.push({ contactId: contact.id, previousId: predecessor.id })
  }
  return ops
}
