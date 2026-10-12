import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

describe('ui store', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.resetModules()
  })

  it('defaults the sidebar to open when nothing is stored', async () => {
    const { useUiStore } = await import('../ui')
    const store = useUiStore()
    expect(store.sidebarOpen).toBe(true)
  })

  it('respects a previously stored closed state', async () => {
    localStorage.setItem('transact-sidebar-open', 'false')
    const { useUiStore } = await import('../ui')
    const store = useUiStore()
    expect(store.sidebarOpen).toBe(false)
  })

  it('toggleSidebar flips state and persists it', async () => {
    const { useUiStore } = await import('../ui')
    const store = useUiStore()

    store.toggleSidebar()
    await Promise.resolve()

    expect(store.sidebarOpen).toBe(false)
    expect(localStorage.getItem('transact-sidebar-open')).toBe('false')
  })
})
