<template>
  <div class="w-full mx-auto px-6 py-10 max-w-[1600px]">
    <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-8">
      <div>
        <h1 class="page-title">My Portfolio</h1>
        <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Manage your investments and import orders
        </p>
      </div>
      <div class="flex gap-3">
        <button
          @click="fetchPrices"
          :disabled="loading || fetchingPrices"
          class="inline-flex items-center justify-center gap-2 bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded-md text-sm font-medium transition disabled:opacity-50"
        >
          <span v-if="!fetchingPrices">Fetch Prices</span>
          <span v-else>Fetching...</span>
        </button>
        <button
          @click="refreshPortfolio"
          :disabled="loading"
          class="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-md text-sm font-medium transition disabled:opacity-50"
        >
          <span v-if="!loading">Refresh</span>
          <span v-else>Loading...</span>
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
        <div class="px-6 py-2 bg-softblue-50 dark:bg-gray-800/40">
          <h3 class="text-sm font-semibold text-softblue-600 dark:text-softblue-400">Index Funds</h3>
        </div>
        <table class="w-full text-sm">
          <thead class="bg-softblue-100 dark:bg-gray-800/80 text-gray-700 dark:text-gray-300">
            <tr class="divide-x divide-gray-200 dark:divide-gray-700">
              <th class="px-4 py-3 text-left font-medium">Symbol</th>
              <th class="px-4 py-3 text-left font-medium">Name</th>
              <th class="px-4 py-3 text-right font-medium">Quantity</th>
              <th class="px-4 py-3 text-right font-medium">Purchase</th>
              <th class="px-4 py-3 text-right font-medium">Current</th>
              <th class="px-4 py-3 text-right font-medium">Value</th>
              <th class="px-4 py-3 text-right font-medium">Gain/Loss</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-softblue-200 dark:divide-gray-700">
            <tr
              v-for="holding in fundHoldings"
              :key="holding.id"
              class="hover:bg-softblue-50 dark:hover:bg-gray-700/40 transition"
            >
              <td class="px-4 py-3 font-medium">{{ holding.resolved_symbol || holding.symbol }}</td>
              <td class="px-4 py-3">{{ holding.name }}</td>
              <td class="px-4 py-3 text-right">{{ holding.quantity }}</td>
              <td class="px-4 py-3 text-right">{{ holding.purchase_price.toFixed(2) }} €</td>
              <td class="px-4 py-3 text-right">
                {{ (holding.current_price || holding.purchase_price).toFixed(2) }} €
              </td>
              <td class="px-4 py-3 text-right">
                {{
                  (holding.quantity * (holding.current_price || holding.purchase_price)).toFixed(2)
                }} €
              </td>
              <td class="px-4 py-3 text-right">
                <span
                  :class="[
                    'inline-flex flex-col items-end px-2 py-1 rounded text-xs font-semibold',
                    getBadgeClass(holding),
                  ]"
                >
                  <span>{{ formatGainLoss(holding) }}</span>
                  <span class="text-[10px] mt-0.5">{{ formatGainLossPercentage(holding) }}</span>
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Crypto Section -->
      <div v-if="cryptoHoldings.length > 0" class="mt-6">
        <div class="px-6 py-2 bg-purple-50 dark:bg-purple-900/20">
          <h3 class="text-sm font-semibold text-purple-600 dark:text-purple-400">Cryptocurrency</h3>
        </div>
        <table class="w-full text-sm">
          <thead class="bg-purple-100 dark:bg-purple-900/30 text-gray-700 dark:text-gray-300">
            <tr class="divide-x divide-gray-200 dark:divide-gray-700">
              <th class="px-4 py-3 text-left font-medium">Symbol</th>
              <th class="px-4 py-3 text-left font-medium">Name</th>
              <th class="px-4 py-3 text-right font-medium">Quantity</th>
              <th class="px-4 py-3 text-right font-medium">Purchase</th>
              <th class="px-4 py-3 text-right font-medium">Current</th>
              <th class="px-4 py-3 text-right font-medium">Value</th>
              <th class="px-4 py-3 text-right font-medium">Gain/Loss</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-purple-200 dark:divide-purple-900/40">
            <tr
              v-for="holding in cryptoHoldings"
              :key="holding.id"
              class="hover:bg-purple-50 dark:hover:bg-purple-900/20 transition"
            >
              <td class="px-4 py-3 font-medium">{{ holding.resolved_symbol || holding.symbol }}</td>
              <td class="px-4 py-3">{{ holding.name }}</td>
              <td class="px-4 py-3 text-right">{{ holding.quantity }}</td>
              <td class="px-4 py-3 text-right">{{ holding.purchase_price.toFixed(2) }} €</td>
              <td class="px-4 py-3 text-right">
                {{ (holding.current_price || holding.purchase_price).toFixed(2) }} €
              </td>
              <td class="px-4 py-3 text-right">
                {{
                  (holding.quantity * (holding.current_price || holding.purchase_price)).toFixed(2)
                }} €
              </td>
              <td class="px-4 py-3 text-right">
                <span
                  :class="[
                    'inline-flex flex-col items-end px-2 py-1 rounded text-xs font-semibold',
                    getBadgeClass(holding),
                  ]"
                >
                  <span>{{ formatGainLoss(holding) }}</span>
                  <span class="text-[10px] mt-0.5">{{ formatGainLossPercentage(holding) }}</span>
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="!fundHoldings.length && !cryptoHoldings.length" class="p-12 text-center">
        <div class="text-gray-400 dark:text-gray-500 mb-2">No investments yet</div>
        <p class="text-xs text-gray-500 dark:text-gray-600">
          Import a CSV or add your first manual order below.
        </p>
      </div>
    </div>

    <!-- CSV Importer -->
    <div class="mb-10">
      <CSVImporter @import-complete="handleImportComplete" />
    </div>

    <!-- Manual Order Form -->
    <div class="mb-10">
      <OrderForm @order-saved="handleOrderSaved" @order-deleted="handleOrderDeleted" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { usePortfolioStore, type Investment } from '@/stores/portfolio'
import { useDashboardStore } from '@/stores/dashboard'
import { useToastStore } from '@/stores/toast'
import { apiClient } from '@/services/api'
import SummaryCard from '@/components/SummaryCard.vue'
import CSVImporter from '@/components/portfolio/CSVImporter.vue'
import OrderForm from '@/components/portfolio/OrderForm.vue'

const portfolioStore = usePortfolioStore()
const toastStore = useToastStore()
const fetchingPrices = ref(false)

const holdings = computed(() => portfolioStore.portfolio?.holdings || [])

// Separate and sort holdings by type and amount
const fundHoldings = computed(() => {
  return holdings.value
    .filter(h => !h.symbol || h.symbol.length > 5) // Exclude crypto (3-5 chars)
    .sort((a, b) => {
      const amountA = a.quantity * a.purchase_price
      const amountB = b.quantity * b.purchase_price
      return amountB - amountA // Descending
    })
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

const loading = computed(() => portfolioStore.loading)
const totalCost = computed(() => portfolioStore.totalCost)
const totalValue = computed(() => portfolioStore.totalValue)
const totalGainLoss = computed(() => portfolioStore.totalGainLoss)

const gainLossClass = computed(() => (totalGainLoss.value >= 0 ? 'text-green-600' : 'text-red-600'))
const gainLossPercentage = computed(() => {
  if (totalCost.value === 0) return 0
  return (totalGainLoss.value / totalCost.value) * 100
})

function getGainLoss(holding: Investment): number {
  const currentPrice = holding.current_price || holding.purchase_price
  return holding.quantity * (currentPrice - holding.purchase_price)
}

function getBadgeClass(holding: Investment): string {
  return getGainLoss(holding) >= 0
    ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300'
    : 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300'
}

function formatGainLoss(holding: Investment): string {
  const v = getGainLoss(holding)
  return `${v >= 0 ? '+' : ''}${v.toFixed(2)} €`
}

function formatGainLossPercentage(holding: Investment): string {
  const totalCost = holding.quantity * holding.purchase_price
  if (totalCost === 0) return '0.00%'
  const gainLoss = getGainLoss(holding)
  const percentage = (gainLoss / totalCost) * 100
  return `${percentage >= 0 ? '+' : ''}${percentage.toFixed(2)}%`
}

async function refreshPortfolio() {
  await portfolioStore.fetchPortfolio()
}

async function handleImportComplete() {
  // Refresh portfolio after successful CSV import
  await refreshPortfolio()
}

async function handleOrderSaved() {
  // Refresh portfolio after manual order is saved
  await refreshPortfolio()
}

async function handleOrderDeleted() {
  // Refresh portfolio after order is deleted
  await refreshPortfolio()
}

async function fetchPrices() {
  fetchingPrices.value = true
  try {
    toastStore.addToast('Fetching prices from Yahoo Finance... This may take 10-15 seconds.', 'info')
    const response = await apiClient.fetchPrices()

    // Wait for background task to complete (with progress updates)
    toastStore.addToast('Processing price data...', 'info')

    setTimeout(async () => {
      await refreshPortfolio()
      const dashboardStore = useDashboardStore()
      await dashboardStore.fetchAll()

      if (response.count && response.count > 0) {
        toastStore.addToast(`Successfully updated prices for ${response.count} instrument(s)`, 'success')
      } else {
        toastStore.addToast('Yahoo Finance may be rate-limiting requests. Prices will use purchase cost as fallback. Try again in a few hours.', 'warning')
      }
    }, 8000) // Increased timeout for sequential fetching
  } catch (error: any) {
    toastStore.addToast(error.response?.data?.detail || 'Failed to fetch prices', 'error')
    fetchingPrices.value = false
  }
}

onMounted(() => {
  portfolioStore.fetchPortfolio()
})
</script>

<style scoped></style>
