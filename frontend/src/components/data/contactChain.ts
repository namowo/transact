import type { InjectionKey, Ref } from 'vue'
import type { Contact } from '@/api/types'

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
