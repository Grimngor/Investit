import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import AuthLayout from '../AuthLayout.vue'

// Mock ThemeToggle to simplify test
vi.mock('../ThemeToggle.vue', () => ({
  default: { template: '<div class="mock-toggle" />' }
}))

describe('AuthLayout theme toggle', () => {
  it('renders theme toggle button', () => {
    const wrapper = mount(AuthLayout, {
      slots: { title: 'Title', default: '<div>Content</div>' }
    })
    expect(wrapper.find('.mock-toggle').exists()).toBe(true)
  })
})
