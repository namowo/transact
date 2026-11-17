import { describe, expect, it } from 'vitest'
import {
  autoLinkDrafts,
  canPlaceIndividual,
  draftRef,
  linkDraft,
  predecessorOptions,
  pruneDraftLinks,
  draftProblem,
  freeSideFor,
  individualSides,
  newContactDraft,
  templateProblem,
} from '../contactBuilder'
import { autoLinkOps, plannedTemplateSequences } from '../contactChain'
import type { Contact, ContactTemplate, Surface } from '@/api/types'

const person = { id: 'st-person' }
const mug = { id: 'st-mug', item_id: 'item-mug' }
const knife = { id: 'st-knife', item_id: 'item-knife' }

function template(
  id: string,
  donor: object | null,
  recipient: object | null,
  previous: string | null = null,
): ContactTemplate {
  return {
    id,
    donor_surface_template: donor,
    recipient_surface_template: recipient,
    previous_contact_template_id: previous,
  } as ContactTemplate
}

const handshake = template('handshake', person, person)
const touchMug = template('touch-mug', person, mug)
const mugToKnife = template('mug-knife', mug, knife)
const sameItem = template('same-item', mug, { id: 'st-mug-2', item_id: 'item-mug' })

describe('contact drafts', () => {
  it('only offers individual slots for individual sides', () => {
    expect(individualSides(handshake)).toEqual(['donor', 'recipient'])
    expect(individualSides(touchMug)).toEqual(['donor'])
    expect(individualSides(mugToKnife)).toEqual([])
  })

  it('does not allow the same individual on both sides of one contact', () => {
    const draft = newContactDraft(handshake.id)
    draft.donorIndividualId = 'a'
    expect(canPlaceIndividual(draft, handshake, 'recipient', 'a')).toBe(false)
    expect(canPlaceIndividual(draft, handshake, 'recipient', 'b')).toBe(true)
    expect(freeSideFor(draft, handshake, 'a')).toBeNull()
    expect(freeSideFor(draft, handshake, 'b')).toBe('recipient')

    draft.recipientIndividualId = 'a'
    expect(draftProblem(draft, handshake)).toMatch(/once per contact/)
  })

  it('does not allow the same item on both sides of one contact', () => {
    expect(templateProblem(sameItem)).toMatch(/once per contact/)
    expect(templateProblem(mugToKnife)).toBeNull()
  })

  it('reports missing individuals and accepts complete drafts', () => {
    const draft = newContactDraft(touchMug.id)
    expect(draftProblem(draft, touchMug)).toBe('Pick the donor.')
    draft.donorIndividualId = 'a'
    expect(draftProblem(draft, touchMug)).toBeNull()
    expect(draftProblem(newContactDraft(mugToKnife.id), mugToKnife)).toBeNull()
  })
})

describe('plannedTemplateSequences', () => {
  it('orders chained templates and keeps unchained ones', () => {
    const a = template('a', person, mug)
    const b = template('b', mug, person, 'a')
    const c = template('c', person, person, 'b')
    const lone = template('lone', person, mug)
    expect(plannedTemplateSequences([c, lone, b, a]).map((s) => s.map((t) => t.id))).toEqual([
      ['lone'],
      ['a', 'b', 'c'],
    ])
  })
})

describe('autoLinkOps', () => {
  const first = template('first', person, mug)
  const second = template('second', mug, person, 'first')
  const surface = (id: string, individualId?: string) => ({ id, individual_id: individualId ?? null }) as Surface

  function contact(id: string, templateId: string, donor: Surface, recipient: Surface, previous?: string): Contact {
    return {
      id,
      contact_template_id: templateId,
      donor_surface: donor,
      recipient_surface: recipient,
      previous_contact_id: previous ?? null,
    }
  }

  it('links contacts sharing an individual, which may recur in a chain', () => {
    const contacts = [
      contact('a1', 'first', surface('sa', 'ann'), surface('mug1')),
      contact('b1', 'first', surface('sb', 'bob'), surface('mug2')),
      contact('a2', 'second', surface('mug3'), surface('sa2', 'ann')),
      contact('b2', 'second', surface('mug4'), surface('sb2', 'bob')),
    ]
    expect(autoLinkOps(contacts, [first, second])).toEqual([
      { contactId: 'a2', previousId: 'a1' },
      { contactId: 'b2', previousId: 'b1' },
    ])
  })

  it('links contacts sharing a surface and never follows a contact twice', () => {
    const mugSurface = surface('mug')
    const contacts = [
      contact('t1', 'first', surface('s1', 'ann'), mugSurface),
      contact('t2', 'second', mugSurface, surface('s2', 'bob')),
      contact('t3', 'second', mugSurface, surface('s3', 'cat')),
    ]
    expect(autoLinkOps(contacts, [first, second])).toEqual([{ contactId: 't2', previousId: 't1' }])
  })

  it('limits proposals to the given contacts', () => {
    const contacts = [
      contact('a1', 'first', surface('sa', 'ann'), surface('m1')),
      contact('a2', 'second', surface('m2'), surface('sa2', 'ann')),
    ]
    expect(autoLinkOps(contacts, [first, second], new Set(['other']))).toEqual([])
    expect(autoLinkOps(contacts, [first, second], new Set(['a1']))).toHaveLength(1)
  })
})

describe('chaining drafts while creating', () => {
  const first = template('first', person, mug)
  const second = template('second', mug, person, 'first')
  const templates = new Map([first, second].map((t) => [t.id, t]))

  function draftWith(t: ContactTemplate, donor: string | null, recipient: string | null) {
    const draft = newContactDraft(t.id)
    draft.donorIndividualId = donor
    draft.recipientIndividualId = recipient
    return draft
  }

  it('links drafts to a predecessor draft sharing an individual', () => {
    const ann1 = draftWith(first, 'ann', null)
    const bob1 = draftWith(first, 'bob', null)
    const bob2 = draftWith(second, null, 'bob')
    const ann2 = draftWith(second, null, 'ann')
    const drafts = [ann1, bob1, bob2, ann2]
    autoLinkDrafts(drafts, [], templates)
    expect(bob2.previousRef).toBe(draftRef(bob1))
    expect(ann2.previousRef).toBe(draftRef(ann1))
    expect(ann1.previousRef).toBeNull()
  })

  it('falls back to a recorded contact that is not followed yet', () => {
    const recorded = [
      { id: 'c1', contact_template_id: 'first', donor_surface: { id: 's1', individual_id: 'ann' } },
      { id: 'c2', contact_template_id: 'second', previous_contact_id: 'c1' },
      { id: 'c3', contact_template_id: 'first', donor_surface: { id: 's3', individual_id: 'ann' } },
    ] as Contact[]
    const ann2 = draftWith(second, null, 'ann')
    autoLinkDrafts([ann2], recorded, templates)
    expect(ann2.previousRef).toBe('contact:c3')
  })

  it('lets a contact be followed only once and respects manual unlinking', () => {
    const ann1 = draftWith(first, 'ann', null)
    const a = draftWith(second, null, 'ann')
    const b = draftWith(second, null, 'bob')
    const drafts = [ann1, a, b]
    autoLinkDrafts(drafts, [], templates)
    expect(a.previousRef).toBe(draftRef(ann1))

    linkDraft(drafts, b, draftRef(ann1))
    expect(b.previousRef).toBe(draftRef(ann1))
    expect(a.previousRef).toBeNull()
    expect(predecessorOptions(a, drafts, [], templates).drafts).toEqual([])

    linkDraft(drafts, b, null)
    autoLinkDrafts(drafts, [], templates)
    expect(b.previousRef).toBeNull()
    expect(a.previousRef).toBe(draftRef(ann1))
  })

  it('drops links to removed drafts', () => {
    const ann1 = draftWith(first, 'ann', null)
    const ann2 = draftWith(second, null, 'ann')
    ann2.previousRef = draftRef(ann1)
    pruneDraftLinks([ann2])
    expect(ann2.previousRef).toBeNull()
  })
})
