import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { apiClient } from '@/services/api'
import { useToastStore } from './toast'

export interface Investment {
  id: number
  symbol: string
  name: string
  quantity: number
  purchase_price: number
  purchase_date: string
  current_price?: number
  asset_type: string
  currency: string
  resolved_symbol?: string
  last_price_timestamp?: string
}

export interface Portfolio {
  username: string
  holdings: Investment[]
}

export const usePortfolioStore = defineStore('portfolio', () => {
  const portfolio = ref<Portfolio | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const totalValue = computed(() => {
    if (!portfolio.value) return 0
    return portfolio.value.holdings.reduce((sum, inv) => {
      const price = inv.current_price || inv.purchase_price
      return sum + inv.quantity * price
    }, 0)
  })

  const totalCost = computed(() => {
    if (!portfolio.value) return 0
    return portfolio.value.holdings.reduce((sum, inv) => {
      return sum + inv.quantity * inv.purchase_price
    }, 0)
  })

  const totalGainLoss = computed(() => totalValue.value - totalCost.value)

  async function fetchPortfolio() {
    loading.value = true
    error.value = null

    try {
      portfolio.value = await apiClient.getPortfolio()
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch portfolio'
      useToastStore().addToast(error.value, 'error')
    } finally {
      loading.value = false
    }
  }

  return {
    portfolio,
    loading,
    error,
    totalValue,
    totalCost,
    totalGainLoss,
    fetchPortfolio
  }
})
