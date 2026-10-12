import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

describe('theme store', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark')
    setActivePinia(createPinia())
  })

  it('defaults to system mode when nothing is stored', async () => {
    const { useThemeStore } = await import('../theme')
    const store = useThemeStore()
    expect(store.mode).toBe('system')
  })

  it('respects a previously stored mode', async () => {
    localStorage.setItem('transact-theme', 'dark')
    vi.resetModules()
    const { useThemeStore } = await import('../theme')
    const store = useThemeStore()
    expect(store.mode).toBe('dark')
    expect(store.isDark).toBe(true)
  })

  it('setMode updates mode, persists it, and toggles the dark class', async () => {
    const { useThemeStore } = await import('../theme')
    const store = useThemeStore()

    store.setMode('dark')
    await Promise.resolve()

    expect(store.mode).toBe('dark')
    expect(store.isDark).toBe(true)
    expect(localStorage.getItem('transact-theme')).toBe('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)

    store.setMode('light')
    await Promise.resolve()

    expect(store.isDark).toBe(false)
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })
})
