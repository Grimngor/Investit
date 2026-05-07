import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'
import { useToastStore } from './toast'
import { API_BASE_URL } from '@/services/config'

// Create axios instance with auth interceptor
const dashboardClient = axios.create({
  baseURL: API_BASE_URL,
})

dashboardClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export interface TimeSeriesDataPoint {
  date: string
  invested_value: number
  current_value: number
}

export interface AllocationData {
  [key: string]: number
}

export interface DashboardAllocations {
  by_instrument: AllocationData
  by_geography: AllocationData
  by_sector: AllocationData
  by_asset_type: AllocationData
}

export interface PriceStatus {
  total_instruments: number
  stale_count: number
  refreshing?: boolean
  stale_instruments: Array<{
    isin: string
    symbol: string
    name: string
    last_price_date: string
    days_stale: number
  }>
}

export interface DashboardKPIs {
  total_invested: number
  current_value: number
  gain_loss: number
  gain_loss_percentage: number
}

export const useDashboardStore = defineStore('dashboard', () => {
  const kpis = ref<DashboardKPIs | null>(null)
  const timeSeries = ref<TimeSeriesDataPoint[]>([])
  const allocations = ref<DashboardAllocations | null>(null)
  const priceStatus = ref<PriceStatus | null>(null)
  const refreshingPrices = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const hasStaleData = computed(() => {
    return priceStatus.value && priceStatus.value.stale_count > 0
  })

  const staleInstruments = computed(() => {
    return priceStatus.value?.stale_instruments || []
  })

  /**
   * Fetch dashboard KPIs (total invested, current value, gain/loss)
   */
  async function fetchKPIs() {
    try {
      const response = await dashboardClient.get('/api/dashboard/kpis')
      kpis.value = response.data
      return response.data
    } catch (err: any) {
      const toastStore = useToastStore()
      toastStore.addToast(err.response?.data?.detail || 'Failed to load dashboard KPIs', 'error')
      throw err
    }
  }

  /**
   * Fetch time series data for line chart (invested vs current value over time)
   */
  async function fetchTimeSeries() {
    loading.value = true
    error.value = null

    try {
      const response = await dashboardClient.get('/api/dashboard/time-series')
      timeSeries.value = response.data.time_series || []
      return response.data
    } catch (err: any) {
      const toastStore = useToastStore()
      error.value = err.response?.data?.detail || 'Failed to load time series data'
      if (error.value) {
        toastStore.addToast(error.value, 'error')
      }
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch allocation data for pie charts (instrument, geography, sector, asset type)
   */
  async function fetchAllocations() {
    loading.value = true
    error.value = null

    try {
      const response = await dashboardClient.get('/api/dashboard/allocations')
      allocations.value = response.data
      return response.data
    } catch (err: any) {
      const toastStore = useToastStore()
      error.value = err.response?.data?.detail || 'Failed to load allocation data'
      if (error.value) {
        toastStore.addToast(error.value, 'error')
      }
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch price status to check for stale prices (> 3 days per PRD)
   */
  async function fetchPriceStatus() {
    try {
      const response = await dashboardClient.get('/api/dashboard/price-status')
      priceStatus.value = response.data
      refreshingPrices.value = Boolean(response.data.refreshing)
      return response.data
    } catch (err: any) {
      const toastStore = useToastStore()
      toastStore.addToast(err.response?.data?.detail || 'Failed to load price status', 'error')
      throw err
    }
  }

  /**
   * Fetch all dashboard data (KPIs, time series, allocations, price status)
   */
  async function fetchAll() {
    loading.value = true
    error.value = null

    try {
      await Promise.all([fetchKPIs(), fetchTimeSeries(), fetchAllocations(), fetchPriceStatus()])
    } catch (err: any) {
      console.error('Error fetching dashboard data:', err)
    } finally {
      loading.value = false
    }
  }

  async function refreshPricesIfNeeded() {
    try {
      const response = await dashboardClient.post('/api/prices/refresh-if-needed')
      refreshingPrices.value = Boolean(response.data.queued || response.data.in_progress)
      return response.data
    } catch (err: any) {
      const toastStore = useToastStore()
      toastStore.addToast(err.response?.data?.detail || 'Failed to check price freshness', 'error')
      throw err
    }
  }

  async function handlePricesUpdated() {
    refreshingPrices.value = false
    await fetchAll()
  }

  /**
   * Refresh dashboard data (call after WebSocket updates)
   */
  async function refresh() {
    await fetchAll()
  }

  function reset() {
    kpis.value = null
    timeSeries.value = []
    allocations.value = null
    priceStatus.value = null
    refreshingPrices.value = false
    loading.value = false
    error.value = null
  }

  return {
    // State
    kpis,
    timeSeries,
    allocations,
    priceStatus,
    refreshingPrices,
    loading,
    error,

    // Computed
    hasStaleData,
    staleInstruments,

    // Actions
    fetchKPIs,
    fetchTimeSeries,
    fetchAllocations,
    fetchPriceStatus,
    fetchAll,
    refreshPricesIfNeeded,
    handlePricesUpdated,
    refresh,
    reset,
  }
})
