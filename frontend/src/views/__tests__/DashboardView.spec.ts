import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DashboardView from '../DashboardView.vue'
import { createPinia } from 'pinia'

describe('DashboardView', () => {
  it('renders dashboard heading', () => {
    const wrapper = mount(DashboardView, { global: { plugins: [createPinia()] } })
    expect(wrapper.text()).toContain('Dashboard')
  })
})
