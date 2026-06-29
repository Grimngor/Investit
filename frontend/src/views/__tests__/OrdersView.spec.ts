import { describe, it, expect, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import OrdersView from '../OrdersView.vue'

vi.mock('@/services/api', () => ({
  apiClient: {
    getOrders: vi.fn().mockResolvedValue({ orders: [], total: 0 }),
    deleteOrder: vi.fn(),
    deleteAllOrders: vi.fn(),
  },
}))

describe('OrdersView', () => {
  it('shows empty state when no orders', async () => {
    const wrapper = mount(OrdersView, {
      global: {
        plugins: [createPinia()],
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('No index fund orders yet')
  })

  it('opens the shared import menu', async () => {
    const wrapper = mount(OrdersView, {
      global: {
        plugins: [createPinia()],
      },
    })

    await flushPromises()

    const importButton = wrapper.findAll('button').find((button) => button.text().includes('Import'))
    await importButton?.trigger('click')

    expect(wrapper.text()).toContain('Import Gmail')
    expect(wrapper.text()).toContain('Import CSV')
    expect(wrapper.text()).toContain('Add Manual Order')
  })
})
