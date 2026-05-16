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
  function mountDashboard() {
    return shallowMount(DashboardView, {
      global: {
        stubs: {
          SummaryCard: { template: '<div />' },
          LineInvestedVsCurrent: { template: '<div />' },
          PieAllocations: {
            props: ['showLegend'],
            template: '<div data-testid="pie-allocation" :data-show-legend="String(showLegend)" />',
          },
        },
      },
    })
  }

  it('renders dashboard heading', () => {
    const wrapper = mountDashboard()
    expect(wrapper.text()).toContain('Dashboard')
  })

  it('shows allocation legends by default on desktop', () => {
    Object.defineProperty(window, 'matchMedia', {
      configurable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: query === '(min-width: 1024px)',
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })),
    })

    const wrapper = mountDashboard()

    expect(wrapper.find('[data-testid="pie-allocation"]').attributes('data-show-legend')).toBe(
      'true',
    )
  })

  it('hides allocation legends by default on mobile', () => {
    Object.defineProperty(window, 'matchMedia', {
      configurable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })),
    })

    const wrapper = mountDashboard()

    expect(wrapper.find('[data-testid="pie-allocation"]').attributes('data-show-legend')).toBe(
      'false',
    )
  })
})
