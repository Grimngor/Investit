<template>
  <div class="max-w-7xl mx-auto px-4 py-8">
    <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-8">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">My Portfolio</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Overview of your current investments</p>
      </div>
      <button
        @click="refreshPortfolio"
        :disabled="loading"
        class="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-md text-sm font-medium transition disabled:opacity-50"
      >
        <span v-if="!loading">Refresh</span>
        <span v-else>Loading...</span>
      </button>
    </div>

    <!-- Summary Cards -->
    <div class="grid gap-4 md:grid-cols-3 mb-10">
      <SummaryCard label="Total Cost" :value="totalCost" prefix="€" />
      <SummaryCard label="Total Value" :value="totalValue" prefix="€" />
      <SummaryCard label="Gain/Loss" :value="totalGainLoss" prefix="€" :value-class="gainLossClass" />
    </div>

    <!-- Holdings Table -->
    <div class="bg-white dark:bg-gray-900/70 backdrop-blur rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 dark:bg-gray-800/80 text-gray-600 dark:text-gray-300">
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
        <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
          <tr
            v-for="holding in holdings"
            :key="holding.id"
            class="hover:bg-gray-50 dark:hover:bg-gray-800/60 transition"
          >
            <td class="px-4 py-3 font-medium">{{ holding.resolved_symbol || holding.symbol }}</td>
            <td class="px-4 py-3">{{ holding.name }}</td>
            <td class="px-4 py-3 text-right">{{ holding.quantity }}</td>
            <td class="px-4 py-3 text-right">€{{ holding.purchase_price.toFixed(2) }}</td>
            <td class="px-4 py-3 text-right">€{{ (holding.current_price || holding.purchase_price).toFixed(2) }}</td>
            <td class="px-4 py-3 text-right">€{{ (holding.quantity * (holding.current_price || holding.purchase_price)).toFixed(2) }}</td>
            <td class="px-4 py-3 text-right">
              <span :class="['inline-flex px-2 py-1 rounded text-xs font-semibold', getBadgeClass(holding)]">
                {{ formatGainLoss(holding) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="!holdings || holdings.length === 0" class="p-12 text-center">
        <div class="text-gray-400 dark:text-gray-500 mb-2">No investments yet</div>
        <p class="text-xs text-gray-500 dark:text-gray-600">Add your first investment to get started.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, defineAsyncComponent } from 'vue'
import { usePortfolioStore, type Investment } from '@/stores/portfolio'

// Lazy load summary card component (can be expanded later for charts etc.)
const SummaryCard = defineAsyncComponent(() => import('@/components/SummaryCard.vue'))

const portfolioStore = usePortfolioStore()

const holdings = computed(() => portfolioStore.portfolio?.holdings || [])
const loading = computed(() => portfolioStore.loading)
const totalCost = computed(() => portfolioStore.totalCost)
const totalValue = computed(() => portfolioStore.totalValue)
const totalGainLoss = computed(() => portfolioStore.totalGainLoss)

const gainLossClass = computed(() => (totalGainLoss.value >= 0 ? 'text-green-600' : 'text-red-600'))

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
  return `${v >= 0 ? '+' : ''}€${v.toFixed(2)}`
}

async function refreshPortfolio() {
  await portfolioStore.fetchPortfolio()
}

onMounted(() => { portfolioStore.fetchPortfolio() })
</script>
