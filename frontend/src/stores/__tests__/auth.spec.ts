import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '../auth'
import * as authApi from '@/api/auth'
import type { User } from '@/api/types'

vi.mock('@/api/auth')
vi.mock('@/api/users', () => ({
  updateMe: vi.fn(),
  dismissPasskeyPrompt: vi.fn(),
  changePassword: vi.fn(),
  changeEmail: vi.fn(),
}))

function makeUser(overrides: Partial<User> = {}): User {
  return {
    id: 'user-1',
    email: 'user@example.com',
    first_name: 'Test',
    last_name: 'User',
    is_active: true,
    is_verified: true,
    is_superuser: false,
    can_quality_check: false,
    can_manage_lab_users: false,
    passkey_prompt_dismissed: false,
    laboratory_id: null,
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  } as User
}

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('starts unauthenticated', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
  })

  it('becomes authenticated after a successful login', async () => {
    vi.mocked(authApi.login).mockResolvedValue(makeUser())
    const store = useAuthStore()

    await store.login('user@example.com', 'Passw0rd!')

    expect(store.isAuthenticated).toBe(true)
    expect(store.user?.email).toBe('user@example.com')
  })

  it('derives isSuperuser from the current user', async () => {
    vi.mocked(authApi.login).mockResolvedValue(makeUser({ is_superuser: true }))
    const store = useAuthStore()

    await store.login('admin@example.com', 'Passw0rd!')

    expect(store.isSuperuser).toBe(true)
    expect(store.canQualityCheck).toBe(true)
    expect(store.isLabAdmin).toBe(true)
  })

  it('clears the user when fetchCurrentUser fails', async () => {
    vi.mocked(authApi.fetchMe).mockRejectedValue(new Error('401'))
    const store = useAuthStore()

    await store.fetchCurrentUser()

    expect(store.user).toBeNull()
  })

  it('memoizes ensureUserLoaded across calls', async () => {
    vi.mocked(authApi.fetchMe).mockResolvedValue(makeUser())
    const store = useAuthStore()

    await Promise.all([store.ensureUserLoaded(), store.ensureUserLoaded()])

    expect(authApi.fetchMe).toHaveBeenCalledTimes(1)
  })

  it('clears user state on handleUnauthorized without calling the API', () => {
    const store = useAuthStore()
    store.user = makeUser()

    store.handleUnauthorized()

    expect(store.user).toBeNull()
    expect(authApi.logout).not.toHaveBeenCalled()
  })

  it('clears user state after logout even if the API call fails', async () => {
    vi.mocked(authApi.logout).mockRejectedValue(new Error('network error'))
    const store = useAuthStore()
    store.user = makeUser()

    await expect(store.logout()).rejects.toThrow()
    expect(store.user).toBeNull()
  })
})
