import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ContactInput, ContactTemplate, SurfaceInput } from '@/api/types'

const created: ContactInput[] = []
const surfaces: SurfaceInput[] = []

vi.mock('@/api/surfaces', () => ({
  createSurface: vi.fn(async (payload: SurfaceInput) => {
    surfaces.push(payload)
    return { id: `surface-${surfaces.length}`, ...payload }
  }),
}))
vi.mock('@/api/contacts', () => ({
  createContact: vi.fn(async (payload: ContactInput) => {
    created.push(payload)
    return { id: `contact-${created.length}`, ...payload }
  }),
}))

const { newContactDraft, draftRef, saveContactDrafts } = await import('../contactBuilder')

const person = { id: 'st-person' }
const mug = { id: 'st-mug', item_id: 'item-mug' }
const first = { id: 'first', donor_surface_template: person, recipient_surface_template: mug } as ContactTemplate
const second = {
  id: 'second',
  donor_surface_template: mug,
  recipient_surface_template: person,
  previous_contact_template_id: 'first',
} as ContactTemplate

describe('saveContactDrafts', () => {
  beforeEach(() => {
    created.length = 0
    surfaces.length = 0
  })

  it('saves predecessors first and links followers to them', async () => {
    const ann1 = newContactDraft('first')
    ann1.donorIndividualId = 'ann'
    const ann2 = newContactDraft('second')
    ann2.recipientIndividualId = 'ann'
    ann2.previousRef = draftRef(ann1)
    const recordedFollower = newContactDraft('second')
    recordedFollower.recipientIndividualId = 'bob'
    recordedFollower.previousRef = 'contact:old'

    // Followers listed first on purpose.
    const result = await saveContactDrafts([ann2, recordedFollower, ann1], [first, second])

    expect(result.error).toBeNull()
    const ann1Index = created.findIndex((c) => c.contact_template_id === 'first')
    const ann2Index = created.findIndex((c) => c.previous_contact_id === `contact-${ann1Index + 1}`)
    expect(created[ann1Index]).toMatchObject({ previous_contact_id: null })
    expect(created[ann2Index]).toMatchObject({ contact_template_id: 'second' })
    expect(ann2Index).toBeGreaterThan(ann1Index)
    expect(created.some((c) => c.previous_contact_id === 'old')).toBe(true)
  })

  it('gives every contact its own item surface', async () => {
    const a = newContactDraft('first')
    a.donorIndividualId = 'ann'
    const b = newContactDraft('first')
    b.donorIndividualId = 'bob'
    await saveContactDrafts([a, b], [first])
    const mugSurfaces = created.map((c) => c.recipient_surface_id)
    expect(new Set(mugSurfaces).size).toBe(2)
  })

  it('does not save a draft whose predecessor draft was not saved', async () => {
    const incomplete = newContactDraft('first')
    const follower = newContactDraft('second')
    follower.recipientIndividualId = 'ann'
    follower.previousRef = draftRef(incomplete)
    const result = await saveContactDrafts([incomplete, follower], [first, second])
    expect(result.saved).toEqual([])
  })
})
