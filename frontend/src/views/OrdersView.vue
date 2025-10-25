<template>
  <div class="w-full mx-auto px-6 py-10 max-w-[1600px]">
    <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-8">
      <div>
        <h1 class="page-title">Orders</h1>
        <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">History of executed orders</p>
      </div>
      <div class="flex gap-3">
        <button
          @click="confirmDeleteAll"
          :disabled="loading || orders.length === 0"
          class="inline-flex items-center justify-center gap-2 bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded-md text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Delete All
        </button>
        <button
          @click="refreshOrders"
          :disabled="loading"
          class="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-md text-sm font-medium transition disabled:opacity-50"
        >
          <span v-if="!loading">Refresh</span>
          <span v-else>Loading...</span>
        </button>
      </div>
    </div>

    <div class="rounded-xl border border-softblue-200 dark:border-gray-700 bg-white dark:bg-gray-800/60 backdrop-blur shadow-sm overflow-hidden">
      <div v-if="loading" class="p-12 text-center">
        <div class="text-gray-500 dark:text-gray-400">Loading orders...</div>
      </div>
      
      <table class="w-full text-sm" v-else-if="orders.length">
        <thead class="bg-softblue-100 dark:bg-gray-800/80 text-gray-700 dark:text-gray-300">
          <tr class="divide-x divide-gray-200 dark:divide-gray-700">
            <th class="px-4 py-3 text-left font-medium">Date</th>
            <th class="px-4 py-3 text-left font-medium">ISIN</th>
            <th class="px-4 py-3 text-left font-medium">Ticker</th>
            <th class="px-4 py-3 text-right font-medium">Shares</th>
            <th class="px-4 py-3 text-right font-medium">Amount (EUR)</th>
            <th class="px-4 py-3 text-right font-medium">Price</th>
            <th class="px-4 py-3 text-right font-medium">Status</th>
            <th class="px-4 py-3 text-center font-medium w-24">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-softblue-200 dark:divide-gray-700">
          <tr v-for="order in orders" :key="order.id" class="hover:bg-softblue-50 dark:hover:bg-gray-700/40 transition">
            <td class="px-4 py-3">{{ formatDate(order.date) }}</td>
            <td class="px-4 py-3 font-mono text-xs">{{ order.isin }}</td>
            <td class="px-4 py-3 font-medium">{{ order.ticker || 'N/A' }}</td>
            <td class="px-4 py-3 text-right">{{ order.shares }}</td>
            <td class="px-4 py-3 text-right">€{{ order.amount_eur?.toFixed(2) || '0.00' }}</td>
            <td class="px-4 py-3 text-right">€{{ calculatePrice(order) }}</td>
            <td class="px-4 py-3 text-right">
              <span 
                :class="[
                  'inline-flex px-2 py-1 rounded text-xs font-semibold',
                  getStatusClass(order.status)
                ]"
              >
                {{ order.status }}
              </span>
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center justify-center gap-2">
                <button
                  @click="editOrder(order)"
                  class="p-1.5 text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/20 rounded transition"
                  title="Edit order"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                <button
                  @click="confirmDelete(order)"
                  class="p-1.5 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20 rounded transition"
                  title="Delete order"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      
      <div v-else class="p-12 text-center">
        <div class="text-gray-400 dark:text-gray-500 mb-2">No orders yet</div>
        <p class="text-xs text-gray-500 dark:text-gray-600">
          Your executed orders will appear here once you import a CSV or add manual orders.
        </p>
      </div>
    </div>

    <!-- Pagination info -->
    <div v-if="total > 0" class="mt-4 text-sm text-gray-600 dark:text-gray-400 text-center">
      Showing {{ orders.length }} of {{ total }} orders
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiClient } from '@/services/api'
import { useToastStore } from '@/stores/toast'

interface Order {
  id?: string
  date: string
  isin: string
  ticker?: string
  shares: number
  amount_eur?: number
  status: string
}

const orders = ref<Order[]>([])
const loading = ref(false)
const total = ref(0)
const toastStore = useToastStore()

function formatDate(dateStr: string): string {
  if (!dateStr) return 'N/A'
  // Date is already in DD/MM/YYYY format from backend
  return dateStr
}

function calculatePrice(order: Order): string {
  if (order.amount_eur && order.shares && order.shares > 0) {
    return (order.amount_eur / order.shares).toFixed(2)
  }
  return '0.00'
}

function getStatusClass(status: string): string {
  const lowerStatus = status?.toLowerCase() || ''
  if (lowerStatus === 'finalizada') {
    return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
  } else if (lowerStatus === 'rechazada') {
    return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
  }
  return 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
}

async function fetchOrders() {
  loading.value = true
  try {
    const response = await apiClient.getOrders({
      sort_by: 'date',
      sort_order: 'desc',
      limit: 100
    })
    orders.value = response.orders || []
    total.value = response.total || 0
  } catch (error: any) {
    toastStore.addToast(error.response?.data?.detail || 'Failed to load orders', 'error')
  } finally {
    loading.value = false
  }
}

async function refreshOrders() {
  await fetchOrders()
}

async function confirmDelete(order: Order) {
  if (!order.id) return
  
  if (confirm(`Delete order for ${order.isin} on ${formatDate(order.date)}?`)) {
    await deleteOrder(order.id)
  }
}

async function deleteOrder(orderId: string) {
  loading.value = true
  try {
    await apiClient.deleteOrder(orderId)
    toastStore.addToast('Order deleted successfully', 'success')
    await fetchOrders()
  } catch (error: any) {
    toastStore.addToast(error.response?.data?.detail || 'Failed to delete order', 'error')
  } finally {
    loading.value = false
  }
}

async function confirmDeleteAll() {
  if (confirm(`Delete all ${orders.value.length} orders? This action cannot be undone.`)) {
    await deleteAllOrders()
  }
}

async function deleteAllOrders() {
  loading.value = true
  try {
    await apiClient.deleteAllOrders()
    toastStore.addToast('All orders deleted successfully', 'success')
    orders.value = []
    total.value = 0
  } catch (error: any) {
    toastStore.addToast(error.response?.data?.detail || 'Failed to delete orders', 'error')
  } finally {
    loading.value = false
  }
}

function editOrder(order: Order) {
  // TODO: Implement edit modal/form
  toastStore.addToast('Edit functionality coming soon', 'info')
  console.log('Edit order:', order)
}

onMounted(() => {
  fetchOrders()
})
</script>

<style scoped></style>
