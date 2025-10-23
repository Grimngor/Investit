import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import OrdersView from '../OrdersView.vue'

describe('OrdersView', () => {
  it('shows empty state when no orders', () => {
    const wrapper = mount(OrdersView)
    expect(wrapper.text()).toContain('No orders yet')
  })
})
