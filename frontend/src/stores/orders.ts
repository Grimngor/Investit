import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'
import { useToastStore } from './toast'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance with auth interceptor
const ordersClient = axios.create({
  baseURL: API_BASE_URL,
})

ordersClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export interface Order {
  id: string
  user_id: string
  date: string
  isin: string
  ticker?: string
  instrument_name?: string
  amount_eur: number
  shares: number
  order_type: 'buy' | 'sell'
  status: string
  notes?: string
  created_at?: string
  updated_at?: string
}

export interface OrdersFilter {
  isin?: string
  ticker?: string
  order_type?: 'buy' | 'sell'
  status?: string
  date_from?: string
  date_to?: string
}

export interface OrdersSort {
  sort_by?: 'date' | 'amount_eur' | 'shares'
  sort_order?: 'asc' | 'desc'
}

export interface OrdersPagination {
  offset?: number
  limit?: number
}

export const useOrdersStore = defineStore('orders', () => {
  const orders = ref<Order[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const totalCount = ref(0)

  // Filter and sort state
  const filters = ref<OrdersFilter>({})
  const sort = ref<OrdersSort>({
    sort_by: 'date',
    sort_order: 'desc',
  })
  const pagination = ref<OrdersPagination>({
    offset: 0,
    limit: 50,
  })

  const hasFilters = computed(() => {
    return Object.keys(filters.value).some((key) => filters.value[key as keyof OrdersFilter])
  })

  /**
   * Fetch orders with current filters, sort, and pagination
   */
  async function fetchOrders() {
    loading.value = true
    error.value = null

    try {
      const params: any = {
        ...filters.value,
        ...sort.value,
        ...pagination.value,
      }

      // Remove undefined/null values
      Object.keys(params).forEach((key) => {
        if (params[key] === undefined || params[key] === null || params[key] === '') {
          delete params[key]
        }
      })

      const response = await ordersClient.get('/api/orders', { params })
      orders.value = response.data.orders || []
      totalCount.value = response.data.total || orders.value.length
      return response.data
    } catch (err: any) {
      const toastStore = useToastStore()
      error.value = err.response?.data?.detail || 'Failed to load orders'
      if (error.value) {
        toastStore.addToast(error.value, 'error')
      }
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Set filters and fetch orders
   */
  async function setFilters(newFilters: OrdersFilter) {
    filters.value = { ...newFilters }
    pagination.value.offset = 0 // Reset to first page
    await fetchOrders()
  }

  /**
   * Clear all filters
   */
  async function clearFilters() {
    filters.value = {}
    pagination.value.offset = 0
    await fetchOrders()
  }

  /**
   * Set sort and fetch orders
   */
  async function setSort(
    sortBy: 'date' | 'amount_eur' | 'shares',
    sortOrder: 'asc' | 'desc' = 'desc',
  ) {
    sort.value = { sort_by: sortBy, sort_order: sortOrder }
    await fetchOrders()
  }

  /**
   * Go to next page
   */
  async function nextPage() {
    const limit = pagination.value.limit || 50
    if (pagination.value.offset! + limit < totalCount.value) {
      pagination.value.offset! += limit
      await fetchOrders()
    }
  }

  /**
   * Go to previous page
   */
  async function previousPage() {
    const limit = pagination.value.limit || 50
    if (pagination.value.offset! > 0) {
      pagination.value.offset = Math.max(0, pagination.value.offset! - limit)
      await fetchOrders()
    }
  }

  /**
   * Calculate running position per instrument (cumulative shares after each order)
   */
  const ordersWithPosition = computed(() => {
    const positionMap: Record<string, number> = {}

    return orders.value.map((order) => {
      const isin = order.isin
      const currentPosition = positionMap[isin] || 0

      // Calculate new position based on order type
      const sharesChange = order.order_type === 'buy' ? order.shares : -order.shares
      const newPosition = currentPosition + sharesChange
      positionMap[isin] = newPosition

      return {
        ...order,
        running_position: newPosition,
        shares_change: sharesChange,
      }
    })
  })

  /**
   * Get average cost per instrument
   */
  function getAverageCost(isin: string): number {
    const instrumentOrders = orders.value.filter((o) => o.isin === isin && o.order_type === 'buy')
    if (instrumentOrders.length === 0) return 0

    const totalCost = instrumentOrders.reduce((sum, o) => sum + Math.abs(o.amount_eur), 0)
    const totalShares = instrumentOrders.reduce((sum, o) => sum + o.shares, 0)

    return totalShares > 0 ? totalCost / totalShares : 0
  }

  function reset() {
    orders.value = []
    filters.value = {}
    sort.value = { sort_by: 'date', sort_order: 'desc' }
    pagination.value = { offset: 0, limit: 50 }
    loading.value = false
    error.value = null
    totalCount.value = 0
  }

  return {
    // State
    orders,
    loading,
    error,
    totalCount,
    filters,
    sort,
    pagination,

    // Computed
    hasFilters,
    ordersWithPosition,

    // Actions
    fetchOrders,
    setFilters,
    clearFilters,
    setSort,
    nextPage,
    previousPage,
    getAverageCost,
    reset,
  }
})
