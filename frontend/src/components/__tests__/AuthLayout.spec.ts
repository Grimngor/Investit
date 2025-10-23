import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import AuthLayout from '../AuthLayout.vue'
declare const window: any

describe('AuthLayout', () => {
  it('renders title and footer slots', () => {
  // Mock matchMedia for theme store usage
  (globalThis as any).window = (globalThis as any).window || {}
  window.matchMedia = window.matchMedia || (() => ({ matches: true, addEventListener: () => {} }))
  const wrapper = mount(AuthLayout, {
      global: { plugins: [createPinia()] },
      slots: {
        title: 'My Title',
        default: '<form><input /></form>',
        footer: 'Footer content'
      }
    })
    expect(wrapper.text()).toContain('My Title')
    expect(wrapper.text()).toContain('Footer content')
    expect(wrapper.find('form').exists()).toBe(true)
  })
})
