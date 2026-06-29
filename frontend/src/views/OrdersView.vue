<template>
  <div class="w-full mx-auto px-6 py-10 max-w-[1600px]">
    <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-8">
      <div>
        <h1 class="page-title">Orders</h1>
        <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">History of executed orders</p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <div class="relative">
          <button
            @click="showImportMenu = !showImportMenu"
            class="action-button action-button--primary"
            type="button"
            aria-haspopup="menu"
            :aria-expanded="showImportMenu"
          >
            <Upload class="h-4 w-4" />
            Import
            <ChevronDown class="h-4 w-4 transition-transform" :class="{ 'rotate-180': showImportMenu }" />
          </button>
          <div
            v-if="showImportMenu"
            class="action-menu"
            role="menu"
            @keydown.esc="showImportMenu = false"
          >
            <button type="button" class="action-menu-item" role="menuitem" @click="openGmailImport">
              <Mail class="h-4 w-4" />
              Import Gmail
            </button>
            <button type="button" class="action-menu-item" role="menuitem" @click="openCsvImport">
              <Upload class="h-4 w-4" />
              Import CSV
            </button>
            <button type="button" class="action-menu-item" role="menuitem" @click="openManualOrder">
              <Plus class="h-4 w-4" />
              Add Manual Order
            </button>
          </div>
        </div>
        <button
          v-if="selectedIds.length > 0"
          @click="confirmDeleteSelected"
          :disabled="loading"
          class="action-button action-button--danger"
        >
          Delete Selected ({{ selectedIds.length }})
        </button>
        <button
          v-else
          @click="confirmDeleteAll"
          :disabled="loading || orders.length === 0"
          class="action-button action-button--danger"
        >
          Delete All
        </button>
        <button
          @click="refreshOrders"
          :disabled="loading"
          class="action-button action-button--secondary"
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
      @saved="handleEditSaved"
    />

    <Teleport to="body">
      <div
        v-if="showImportModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
        @click.self="showImportModal = false"
      >
        <div
          class="m-4 max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-xl bg-white p-4 shadow-xl dark:bg-gray-800 sm:p-6"
          role="dialog"
          aria-modal="true"
          aria-labelledby="orders-csv-import-title"
        >
          <div class="mb-6 flex items-start justify-between gap-4">
            <h2 id="orders-csv-import-title" class="text-xl font-semibold text-gray-800 dark:text-gray-200">
              Import Orders from CSV
            </h2>
            <button
              @click="showImportModal = false"
              class="rounded p-1 text-gray-400 transition hover:text-gray-600 dark:hover:text-gray-300"
              aria-label="Close CSV import"
            >
              <X class="h-6 w-6" />
            </button>
          </div>
          <CSVImporter embedded :show-title="false" @import-complete="handleImportComplete" />
        </div>
      </div>

      <div
        v-if="showOrderModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
        @click.self="showOrderModal = false"
      >
        <div
          class="m-4 max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl bg-white p-4 shadow-xl dark:bg-gray-800 sm:p-6"
          role="dialog"
          aria-modal="true"
          aria-labelledby="orders-manual-order-title"
        >
          <div class="mb-6 flex items-start justify-between gap-4">
            <h2 id="orders-manual-order-title" class="text-xl font-semibold text-gray-800 dark:text-gray-200">
              Add Manual Order
            </h2>
            <button
              @click="showOrderModal = false"
              class="rounded p-1 text-gray-400 transition hover:text-gray-600 dark:hover:text-gray-300"
              aria-label="Close manual order"
            >
              <X class="h-6 w-6" />
            </button>
          </div>
          <OrderForm
            embedded
            :show-title="false"
            @order-saved="handleOrderSaved"
            @order-deleted="handleOrderDeleted"
          />
        </div>
      </div>

      <GmailImportModal
        :show="showGmailImportModal"
        @close="showGmailImportModal = false"
        @import-complete="handleGmailImportComplete"
      />
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { apiClient } from '@/services/api'
import { useToastStore } from '@/stores/toast'
import CSVImporter from '@/components/portfolio/CSVImporter.vue'
import GmailImportModal from '@/components/portfolio/GmailImportModal.vue'
import OrderForm from '@/components/portfolio/OrderForm.vue'
import OrderEditModal from '@/components/orders/OrderEditModal.vue'
import OrdersTable from '@/components/orders/OrdersTable.vue'
import { ChevronDown, Mail, Plus, Upload, X } from 'lucide-vue-next'

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
const showGmailImportModal = ref(false)
const showImportMenu = ref(false)
const showImportModal = ref(false)
const showOrderModal = ref(false)
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

function openGmailImport() {
  showImportMenu.value = false
  showGmailImportModal.value = true
}

function openCsvImport() {
  showImportMenu.value = false
  showImportModal.value = true
}

function openManualOrder() {
  showImportMenu.value = false
  showOrderModal.value = true
}

async function handleImportComplete() {
  showImportModal.value = false
  await fetchOrders()
}

async function handleGmailImportComplete() {
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
  showOrderModal.value = false
  await fetchOrders()
}

async function handleOrderDeleted() {
  showOrderModal.value = false
  await fetchOrders()
}

async function handleEditSaved() {
  await fetchOrders()
}

onMounted(() => {
  fetchOrders()
})
</script>

<style scoped></style>
