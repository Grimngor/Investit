import { describe, it, expect, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import DashboardView from '../DashboardView.vue'

vi.mock('@/stores/portfolio', () => ({
  usePortfolioStore: () => ({
    totalCost: 0,
    totalValue: 0,
    totalGainLoss: 0,
    fetchPortfolio: vi.fn(),
  }),
}))

vi.mock('@/stores/dashboard', () => ({
  useDashboardStore: () => ({
    loading: false,
    timeSeries: [],
    allocations: null,
    hasStaleData: false,
    priceStatus: null,
    refreshingPrices: false,
    staleInstruments: [],
    fetchAll: vi.fn(),
    refreshPricesIfNeeded: vi.fn(),
    handlePricesUpdated: vi.fn(),
  }),
}))

vi.mock('@/services/websocket', () => ({
  wsClient: {
    on: vi.fn(),
    off: vi.fn(),
  },
}))

describe('DashboardView', () => {
  it('renders dashboard heading', () => {
    const wrapper = shallowMount(DashboardView, {
      global: {
        stubs: {
          SummaryCard: { template: '<div />' },
          LineInvestedVsCurrent: { template: '<div />' },
          PieAllocations: { template: '<div />' },
        },
      },
    })
    expect(wrapper.text()).toContain('Dashboard')
  })
})
