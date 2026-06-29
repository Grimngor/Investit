<template>
  <div class="w-full mx-auto px-6 py-10 max-w-[1600px]">
    <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-8">
      <div>
        <h1 class="page-title">My Portfolio</h1>
        <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Manage your investments and import orders
        </p>
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
          @click="fetchPrices"
          :disabled="loading || fetchingPrices"
          class="action-button action-button--secondary"
        >
          <CircleDollarSign class="h-4 w-4" />
          <span v-if="!fetchingPrices">Fetch Prices</span>
          <span v-else>Fetching...</span>
        </button>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="grid gap-4 md:grid-cols-3 mb-10">
      <SummaryCard label="Total Invested" :value="totalCost" suffix="€" />
      <SummaryCard label="Current Value" :value="totalValue" suffix="€" />
      <SummaryCard
        label="Gain / Loss"
        :value="totalGainLoss"
        suffix="€"
        :value-class="gainLossClass"
        :show-sign="true"
        :percentage="gainLossPercentage"
      />
    </div>

    <!-- Holdings Table -->
    <div
      class="rounded-xl border border-softblue-200 dark:border-gray-700 bg-white dark:bg-gray-800/60 backdrop-blur shadow-sm overflow-hidden mb-10"
    >
      <div class="px-6 py-4 border-b border-softblue-200 dark:border-gray-700">
        <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200">Current Holdings</h2>
      </div>

      <!-- Index Funds Section -->
      <div v-if="fundHoldings.length > 0">
        <button
          @click="showIndexFunds = !showIndexFunds"
          class="w-full px-6 py-4 flex items-center justify-between bg-softblue-50 dark:bg-gray-800/40 hover:bg-softblue-100 dark:hover:bg-gray-700/60 transition"
        >
          <div class="flex items-center gap-2">
            <h3 class="text-sm font-semibold text-softblue-700 dark:text-softblue-300">
              Index Funds
            </h3>
            <span class="text-xs font-medium px-2 py-0.5 rounded-full bg-softblue-200 dark:bg-gray-700 text-softblue-800 dark:text-gray-300">
              {{ fundHoldings.length }}
            </span>
          </div>
          <div class="flex items-center gap-4">
            <span class="text-right text-sm font-semibold text-gray-700 dark:text-gray-300">
              {{ indexFundsValue.toFixed(2) }} €
            </span>
            <ChevronDown
              class="w-5 h-5 text-gray-400 transition-transform duration-200"
              :class="{ 'rotate-180': showIndexFunds }"
            />
          </div>
        </button>
        <div v-show="showIndexFunds" data-testid="index-funds-holdings">
          <HoldingsTable
            :holdings="fundHoldings"
            theme="softblue"
            :loading="loading || fetchingPrices"
          />
        </div>
      </div>

      <!-- Crypto Section -->
      <div v-if="cryptoHoldings.length > 0" class="mt-2 lg:mt-6">
        <button
          @click="showCrypto = !showCrypto"
          class="w-full px-6 py-4 flex items-center justify-between bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 dark:hover:bg-purple-900/40 transition"
        >
          <div class="flex items-center gap-2">
            <h3 class="text-sm font-semibold text-purple-700 dark:text-purple-300">
              Cryptocurrency
            </h3>
            <span class="text-xs font-medium px-2 py-0.5 rounded-full bg-purple-200 dark:bg-purple-800/60 text-purple-800 dark:text-purple-200">
              {{ cryptoHoldings.length }}
            </span>
          </div>
          <div class="flex items-center gap-4">
            <span class="text-right text-sm font-semibold text-gray-700 dark:text-gray-300">
              {{ cryptoValue.toFixed(2) }} €
            </span>
            <ChevronDown
              class="w-5 h-5 text-gray-400 transition-transform duration-200"
              :class="{ 'rotate-180': showCrypto }"
            />
          </div>
        </button>
        <div v-show="showCrypto" data-testid="crypto-holdings">
          <HoldingsTable
            :holdings="cryptoHoldings"
            theme="purple"
            :loading="loading || fetchingPrices"
          />
        </div>
      </div>

      <div v-if="!fundHoldings.length && !cryptoHoldings.length" class="p-12 text-center">
        <div class="text-gray-400 dark:text-gray-500 mb-2">No investments yet</div>
        <p class="text-xs text-gray-500 dark:text-gray-600">
          Import a CSV or add your first manual order from the page actions.
        </p>
      </div>
    </div>

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
          aria-labelledby="csv-import-title"
        >
          <div class="mb-6 flex items-start justify-between gap-4">
            <div>
              <h2 id="csv-import-title" class="text-xl font-semibold text-gray-800 dark:text-gray-200">
                Import Orders from CSV
              </h2>
            </div>
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
          aria-labelledby="manual-order-title"
        >
          <div class="mb-6 flex items-start justify-between gap-4">
            <h2 id="manual-order-title" class="text-xl font-semibold text-gray-800 dark:text-gray-200">
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
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePortfolioStore } from '@/stores/portfolio'
import { useDashboardStore } from '@/stores/dashboard'
import { useToastStore } from '@/stores/toast'
import { apiClient } from '@/services/api'
import { wsClient } from '@/services/websocket'
import SummaryCard from '@/components/SummaryCard.vue'
import CSVImporter from '@/components/portfolio/CSVImporter.vue'
import GmailImportModal from '@/components/portfolio/GmailImportModal.vue'
import OrderForm from '@/components/portfolio/OrderForm.vue'
import HoldingsTable from '@/components/portfolio/HoldingsTable.vue'
import { ChevronDown, CircleDollarSign, Mail, Plus, Upload, X } from 'lucide-vue-next'

const portfolioStore = usePortfolioStore()
const toastStore = useToastStore()
const route = useRoute()
const router = useRouter()
const fetchingPrices = ref(false)
const showImportModal = ref(false)
const showGmailImportModal = ref(false)
const showOrderModal = ref(false)
const showImportMenu = ref(false)

const holdings = computed(() => portfolioStore.portfolio?.holdings || [])

const fundHoldings = computed(() => {
  return holdings.value
    .filter(h => !h.symbol || h.symbol.length > 5) // Exclude crypto (3-5 chars)
    .sort((a, b) => {
      const amountA = a.quantity * a.purchase_price
      const amountB = b.quantity * b.purchase_price
      return amountB - amountA // Descending
    })
})

const indexFundsValue = computed(() => {
  return fundHoldings.value.reduce((acc, h) => acc + (h.quantity * (h.current_price || h.purchase_price)), 0)
})

const cryptoHoldings = computed(() => {
  return holdings.value
    .filter(h => h.symbol && h.symbol.length >= 3 && h.symbol.length <= 5)
    .sort((a, b) => {
      const amountA = a.quantity * a.purchase_price
      const amountB = b.quantity * b.purchase_price
      return amountB - amountA // Descending
    })
})

const cryptoValue = computed(() => {
  return cryptoHoldings.value.reduce((acc, h) => acc + (h.quantity * (h.current_price || h.purchase_price)), 0)
})

const showIndexFunds = ref(true)
const showCrypto = ref(true)

const loading = computed(() => portfolioStore.loading)
const totalCost = computed(() => portfolioStore.totalCost)
const totalValue = computed(() => portfolioStore.totalValue)
const totalGainLoss = computed(() => portfolioStore.totalGainLoss)

const gainLossClass = computed(() => (totalGainLoss.value >= 0 ? 'text-green-600' : 'text-red-600'))
const gainLossPercentage = computed(() => {
  if (totalCost.value === 0) return 0
  return (totalGainLoss.value / totalCost.value) * 100
})



async function refreshPortfolio() {
  await portfolioStore.fetchPortfolio()
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
  await refreshPortfolio()
}

async function handleGmailImportComplete() {
  await refreshPortfolio()
}

async function handleOrderSaved() {
  showOrderModal.value = false
  await refreshPortfolio()
}

async function handleOrderDeleted() {
  showOrderModal.value = false
  await refreshPortfolio()
}

async function fetchPrices() {
  fetchingPrices.value = true
  try {
    toastStore.addToast('Fetching prices from Yahoo Finance... This may take 10-15 seconds.', 'info')
    const response = await apiClient.fetchPrices()

    if (response.count && response.count > 0) {
      toastStore.addToast('Processing price data...', 'info')
    } else {
      fetchingPrices.value = false
      toastStore.addToast('No instruments found to fetch prices for.', 'warning')
    }
  } catch (error: any) {
    toastStore.addToast(error.response?.data?.detail || 'Failed to fetch prices', 'error')
    fetchingPrices.value = false
  }
}

async function handlePricesUpdated(data: any) {
  fetchingPrices.value = false
  await refreshPortfolio()
  const dashboardStore = useDashboardStore()
  await dashboardStore.fetchAll()

  if (data.count && data.count > 0) {
    toastStore.addToast(`Successfully updated prices for ${data.count} instrument(s)`, 'success')
  } else {
    toastStore.addToast('Yahoo Finance may be rate-limiting requests. Prices will use purchase cost as fallback. Try again later.', 'warning')
  }
}

async function handleOrdersChanged() {
  await refreshPortfolio()
  const dashboardStore = useDashboardStore()
  await dashboardStore.fetchAll()
}

onMounted(() => {
  wsClient.on('prices_updated', handlePricesUpdated)
  wsClient.on('orders_imported', handleOrdersChanged)
  wsClient.on('order_created', handleOrdersChanged)
  wsClient.on('order_updated', handleOrdersChanged)
  wsClient.on('order_deleted', handleOrdersChanged)
  wsClient.on('orders_cleared', handleOrdersChanged)
  portfolioStore.fetchPortfolio()
  handleGmailCallbackToast()
})

onUnmounted(() => {
  wsClient.off('prices_updated', handlePricesUpdated)
  wsClient.off('orders_imported', handleOrdersChanged)
  wsClient.off('order_created', handleOrdersChanged)
  wsClient.off('order_updated', handleOrdersChanged)
  wsClient.off('order_deleted', handleOrdersChanged)
  wsClient.off('orders_cleared', handleOrdersChanged)
})

function handleGmailCallbackToast() {
  if (route.query.gmail === 'connected') {
    toastStore.addToast('Gmail connected', 'success')
    showGmailImportModal.value = true
    router.replace({ path: route.path, query: withoutGmailQuery() })
  } else if (route.query.gmail === 'error') {
    const message = typeof route.query.message === 'string' ? route.query.message : 'Failed to connect Gmail'
    toastStore.addToast(message, 'error')
    router.replace({ path: route.path, query: withoutGmailQuery() })
  }
}

function withoutGmailQuery() {
  const query = { ...route.query }
  delete query.gmail
  delete query.message
  return query
}
</script>

<style scoped></style>
