import { setActivePinia, createPinia } from 'pinia'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useThemeStore } from '../theme'

declare const window: any

describe('theme store', () => {
  beforeEach(() => {
    // Clear localStorage mock
    localStorage.clear()
    // Provide matchMedia mock for store init
    ;(globalThis as any).window = (globalThis as any).window || {}
    ;(globalThis as any).window.matchMedia = vi.fn().mockReturnValue({
      matches: true,
      addEventListener: vi.fn(),
    })
    setActivePinia(createPinia())
  })

  it('defaults to dark when no preference stored', () => {
    const store = useThemeStore()
    expect(store.theme).toBe('dark')
  })

  it('persists theme changes', () => {
    const store = useThemeStore()
    store.setTheme('light')
    expect(localStorage.getItem('theme')).toBe('light')
    store.setTheme('dark')
    expect(localStorage.getItem('theme')).toBe('dark')
  })

  it('toggles between dark and light', () => {
    const store = useThemeStore()
    const initial = store.theme
    store.toggleTheme()
    expect(store.theme).not.toBe(initial)
    store.toggleTheme()
    // Should return to initial theme
    expect(store.theme).toBe(initial)
  })

  it('honors auto mode based on system preference', () => {
    const store = useThemeStore()
    store.setTheme('auto')
    expect(store.isDark).toBe(true)
  })
})
