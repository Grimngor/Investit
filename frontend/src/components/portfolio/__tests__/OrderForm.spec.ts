import { flushPromises, mount } from '@vue/test-utils'
import type { VueWrapper } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import OrderForm from '../OrderForm.vue'

const mocks = vi.hoisted(() => ({
  addToast: vi.fn(),
  deleteOrder: vi.fn(),
  postOrder: vi.fn(),
  putOrder: vi.fn(),
}))

vi.mock('axios', () => ({
  default: {
    delete: mocks.deleteOrder,
    post: mocks.postOrder,
    put: mocks.putOrder,
  },
}))

vi.mock('@/stores/toast', () => ({
  useToastStore: () => ({
    addToast: mocks.addToast,
  }),
}))

function mountForm(props = {}) {
  return mount(OrderForm, { props })
}

async function fillRequiredFields(wrapper: VueWrapper, amount: string) {
  const inputs = wrapper.findAll('input')

  await inputs[0].setValue('2024-01-15')
  await inputs[1].setValue('IE00TEST0001')
  await inputs[2].setValue(amount)
  await inputs[3].setValue('10')
}

describe('OrderForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('token', 'test-token')
    mocks.postOrder.mockResolvedValue({ data: {} })
    mocks.putOrder.mockResolvedValue({ data: {} })
  })

  it('posts positive manual orders as buys', async () => {
    const wrapper = mountForm()

    await fillRequiredFields(wrapper, '300')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(mocks.postOrder).toHaveBeenCalledWith(
      expect.stringContaining('/api/orders'),
      expect.objectContaining({
        amount_eur: 300,
        order_type: 'buy',
      }),
      expect.any(Object),
    )
  })

  it('posts negative manual orders as sells with a positive amount', async () => {
    const wrapper = mountForm()

    await fillRequiredFields(wrapper, '-300')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(mocks.postOrder).toHaveBeenCalledWith(
      expect.stringContaining('/api/orders'),
      expect.objectContaining({
        amount_eur: 300,
        order_type: 'sell',
      }),
      expect.any(Object),
    )
  })

  it('preserves sell order type when editing an existing sell order', async () => {
    const wrapper = mountForm({
      order: {
        id: 'order-1',
        date: '2024-01-15',
        isin: 'IE00TEST0001',
        amount_eur: 300,
        shares: 10,
        status: 'Finalizada',
        notes: '',
        order_type: 'sell',
      },
    })

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(mocks.putOrder).toHaveBeenCalledWith(
      expect.stringContaining('/api/orders/order-1'),
      expect.objectContaining({
        amount_eur: 300,
        order_type: 'sell',
      }),
      expect.any(Object),
    )
  })
})
