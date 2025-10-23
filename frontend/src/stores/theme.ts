import { ref, watch } from 'vue'
import { defineStore } from 'pinia'

export type Theme = 'light' | 'dark' | 'auto'

export const useThemeStore = defineStore('theme', () => {
  // Initialize from localStorage or default to 'auto'
  const theme = ref<Theme>((localStorage.getItem('theme') as Theme) || 'auto')
  const isDark = ref(false)

  /**
   * Get system preference
   */
  const getSystemPreference = (): boolean => {
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  }

  /**
   * Apply theme to document
   */
  const applyTheme = (themeName: Theme) => {
    let shouldBeDark = false

    if (themeName === 'auto') {
      shouldBeDark = getSystemPreference()
    } else {
      shouldBeDark = themeName === 'dark'
    }

    isDark.value = shouldBeDark

    if (shouldBeDark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  /**
   * Set theme
   */
  const setTheme = (newTheme: Theme) => {
    theme.value = newTheme
    localStorage.setItem('theme', newTheme)
    applyTheme(newTheme)
  }

  /**
   * Toggle between light and dark
   */
  const toggleTheme = () => {
    if (theme.value === 'auto') {
      setTheme(isDark.value ? 'light' : 'dark')
    } else {
      setTheme(theme.value === 'dark' ? 'light' : 'dark')
    }
  }

  // Watch for system preference changes
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  mediaQuery.addEventListener('change', () => {
    if (theme.value === 'auto') {
      applyTheme('auto')
    }
  })

  // Watch theme changes
  watch(
    theme,
    (newTheme) => {
      applyTheme(newTheme)
    },
    { immediate: true },
  )

  return {
    theme,
    isDark,
    setTheme,
    toggleTheme,
  }
})
