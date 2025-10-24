<template>
  <div class="max-w-7xl mx-auto px-6 py-10">
    <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-8">
      <div>
        <h1 class="page-title">My Portfolio</h1>
        <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Manage your investments and import orders
        </p>
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
      <SummaryCard
        label="Gain/Loss"
        :value="totalGainLoss"
        prefix="€"
        :value-class="gainLossClass"
      />
    </div>

    <!-- CSV Importer -->
    <div class="mb-10">
      <CSVImporter @import-complete="handleImportComplete" />
    </div>

    <!-- Manual Order Form -->
    <div class="mb-10">
      <OrderForm @order-saved="handleOrderSaved" @order-deleted="handleOrderDeleted" />
    </div>

    <!-- Holdings Table -->
    <div
      class="rounded-xl border border-softblue-200 dark:border-gray-700 bg-white dark:bg-gray-800/60 backdrop-blur shadow-sm overflow-hidden"
    >
      <div class="px-6 py-4 border-b border-softblue-200 dark:border-gray-700">
        <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200">Current Holdings</h2>
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
            v-for="holding in holdings"
            :key="holding.id"
            class="hover:bg-softblue-50 dark:hover:bg-gray-700/40 transition"
          >
            <td class="px-4 py-3 font-medium">{{ holding.resolved_symbol || holding.symbol }}</td>
            <td class="px-4 py-3">{{ holding.name }}</td>
            <td class="px-4 py-3 text-right">{{ holding.quantity }}</td>
            <td class="px-4 py-3 text-right">€{{ holding.purchase_price.toFixed(2) }}</td>
            <td class="px-4 py-3 text-right">
              €{{ (holding.current_price || holding.purchase_price).toFixed(2) }}
            </td>
            <td class="px-4 py-3 text-right">
              €{{
                (holding.quantity * (holding.current_price || holding.purchase_price)).toFixed(2)
              }}
            </td>
            <td class="px-4 py-3 text-right">
              <span
                :class="[
                  'inline-flex px-2 py-1 rounded text-xs font-semibold',
                  getBadgeClass(holding),
                ]"
              >
                {{ formatGainLoss(holding) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="!holdings || holdings.length === 0" class="p-12 text-center">
        <div class="text-gray-400 dark:text-gray-500 mb-2">No investments yet</div>
        <p class="text-xs text-gray-500 dark:text-gray-600">
          Import a CSV or add your first manual order above.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { usePortfolioStore, type Investment } from '@/stores/portfolio'
import SummaryCard from '@/components/SummaryCard.vue'
import CSVImporter from '@/components/portfolio/CSVImporter.vue'
import OrderForm from '@/components/portfolio/OrderForm.vue'

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

onMounted(() => {
  portfolioStore.fetchPortfolio()
})
</script>

<style scoped></style>
