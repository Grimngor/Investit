import { shallowMount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import PortfolioView from '../PortfolioView.vue'

vi.mock('@/stores/portfolio', () => ({
  usePortfolioStore: () => ({
    portfolio: { holdings: [] },
    loading: false,
    totalCost: 0,
    totalValue: 0,
    totalGainLoss: 0,
    fetchPortfolio: vi.fn(),
  }),
}))

vi.mock('@/stores/dashboard', () => ({
  useDashboardStore: () => ({
    fetchAll: vi.fn(),
  }),
}))

vi.mock('@/stores/toast', () => ({
  useToastStore: () => ({
    addToast: vi.fn(),
  }),
}))

vi.mock('@/services/api', () => ({
  apiClient: {
    fetchPrices: vi.fn(),
  },
}))

vi.mock('@/services/websocket', () => ({
  wsClient: {
    on: vi.fn(),
    off: vi.fn(),
  },
}))

function mountView() {
  return shallowMount(PortfolioView, {
    global: {
      stubs: {
        SummaryCard: { template: '<div data-testid="summary-card" />' },
        HoldingsTable: true,
        CSVImporter: { template: '<div data-testid="csv-importer" />' },
        OrderForm: { template: '<div data-testid="order-form" />' },
        Teleport: true,
      },
    },
  })
}

describe('PortfolioView', () => {
  it('opens the CSV import modal from the page action', async () => {
    const wrapper = mountView()

    const importButton = wrapper.findAll('button').find((button) => button.text() === 'Import CSV')
    await importButton?.trigger('click')

    expect(wrapper.get('[data-testid="csv-importer"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Import Orders from CSV')
  })

  it('opens the manual order modal from the page action', async () => {
    const wrapper = mountView()

    const orderButton = wrapper.findAll('button').find((button) => button.text() === 'Add Manual Order')
    await orderButton?.trigger('click')

    expect(wrapper.get('[data-testid="order-form"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Add Manual Order')
  })
})
