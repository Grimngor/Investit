<template>
  <div class="w-full mx-auto px-6 py-10 max-w-[1600px]">
    <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-8">
      <div>
        <h1 class="page-title">Orders</h1>
        <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">History of executed orders</p>
      </div>
      <div class="flex flex-wrap gap-3">
        <button
          v-if="selectedIds.length > 0"
          @click="confirmDeleteSelected"
          :disabled="loading"
          class="inline-flex items-center justify-center gap-2 bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded-md text-sm font-medium transition disabled:opacity-50"
        >
          Delete Selected ({{ selectedIds.length }})
        </button>
        <button
          v-else
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

    <!-- Index Fund Orders Table -->
    <OrdersTable
      title="Index Fund Orders"
      :orders="indexFundOrders"
      :loading="loading"
      emptyMessage="No index fund orders yet"
      @edit="editOrder"
      @delete="confirmDelete"
      @selection-change="handleIndexFundSelection"
    />

    <!-- Crypto Orders Table -->
    <OrdersTable
      v-if="cryptoOrders.length > 0"
      title="Crypto Orders"
      :orders="cryptoOrders"
      :loading="loading"
      emptyMessage="No crypto orders yet"
      @edit="editOrder"
      @delete="confirmDelete"
      @selection-change="handleCryptoSelection"
      class="border-purple-200 dark:border-purple-800"
    />



    <!-- Pagination info -->
    <div v-if="total > 0" class="mt-4 text-sm text-gray-600 dark:text-gray-400 text-center">
      Showing {{ orders.length }} of {{ total }} orders
    </div>

    <!-- Edit Modal -->
    <OrderEditModal
      :order="selectedOrder"
      :is-open="showEditModal"
      @close="closeEditModal"
      @saved="handleOrderSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { apiClient } from '@/services/api'
import { useToastStore } from '@/stores/toast'
import OrderEditModal from '@/components/orders/OrderEditModal.vue'
import OrdersTable from '@/components/orders/OrdersTable.vue'

interface Order {
  id?: string
  date: string
  isin: string
  ticker?: string
  shares: number
  amount_eur?: number
  status: string
  asset_type?: string
}

const orders = ref<Order[]>([])
const total = ref(0)
const loading = ref(false)

const selectedIndexFundIds = ref<string[]>([])
const selectedCryptoIds = ref<string[]>([])

const selectedIds = computed(() => {
  return [...selectedIndexFundIds.value, ...selectedCryptoIds.value]
})

// Separate orders by asset type
const indexFundOrders = computed(() => orders.value.filter(o => o.asset_type !== 'Crypto'))
const cryptoOrders = computed(() => orders.value.filter(o => o.asset_type === 'Crypto'))
const toastStore = useToastStore()
const showEditModal = ref(false)
const selectedOrder = ref<Order | null>(null)

function handleIndexFundSelection(ids: string[]) {
  selectedIndexFundIds.value = ids
}

function handleCryptoSelection(ids: string[]) {
  selectedCryptoIds.value = ids
}

function formatDate(dateStr: string): string {
  if (!dateStr) return 'N/A'
  return dateStr
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

async function confirmDeleteSelected() {
  if (selectedIds.value.length === 0) return

  if (confirm(`Delete ${selectedIds.value.length} selected orders?`)) {
    await deleteSelectedOrders()
  }
}

async function deleteSelectedOrders() {
  loading.value = true
  try {
    for (const id of selectedIds.value) {
      await apiClient.deleteOrder(id)
    }
    toastStore.addToast(`Successfully deleted ${selectedIds.value.length} orders`, 'success')
    selectedIndexFundIds.value = []
    selectedCryptoIds.value = []
    await fetchOrders()
  } catch (error: any) {
    toastStore.addToast('Failed to delete some orders', 'error')
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
  selectedOrder.value = order
  showEditModal.value = true
}

function closeEditModal() {
  showEditModal.value = false
  selectedOrder.value = null
}

async function handleOrderSaved() {
  await fetchOrders()
}

onMounted(() => {
  fetchOrders()
})
</script>

<style scoped></style>
