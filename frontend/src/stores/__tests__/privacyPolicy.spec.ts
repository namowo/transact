import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { usePrivacyPolicyStore } from '../privacyPolicy'
import { privacyPolicyApi } from '@/api/privacyPolicy'
import type { PrivacyPolicy, User } from '@/api/types'

vi.mock('@/api/privacyPolicy', () => ({
  privacyPolicyApi: { getActive: vi.fn() },
}))

const policy: PrivacyPolicy = {
  id: 7,
  version: 2,
  mode: 'text',
  text: '<p>Policy</p>',
  url: null,
  published_at: '2026-11-01T00:00:00Z',
}

function user(accepted: number[]): User {
  return { accepted_privacy_policy_ids: accepted } as User
}

describe('privacy policy store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('needs no consent while no policy is published', async () => {
    vi.mocked(privacyPolicyApi.getActive).mockResolvedValue(null)
    const store = usePrivacyPolicyStore()
    await store.load()
    expect(store.needsConsent(user([]))).toBe(false)
  })

  it('needs consent until the user agreed to the active version', async () => {
    vi.mocked(privacyPolicyApi.getActive).mockResolvedValue(policy)
    const store = usePrivacyPolicyStore()
    await store.load()
    expect(store.needsConsent(user([]))).toBe(true)
    expect(store.needsConsent(user([3]))).toBe(true)
    expect(store.needsConsent(user([3, 7]))).toBe(false)
    expect(store.needsConsent(null)).toBe(false)
  })

  it('loads once unless forced', async () => {
    vi.mocked(privacyPolicyApi.getActive).mockResolvedValue(policy)
    const store = usePrivacyPolicyStore()
    await store.load()
    await store.load()
    expect(privacyPolicyApi.getActive).toHaveBeenCalledTimes(1)
    await store.load(true)
    expect(privacyPolicyApi.getActive).toHaveBeenCalledTimes(2)
  })
})
