<template>
  <div class="container mx-auto px-4 py-8">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-bold">My Portfolio</h1>
      <button
        @click="refreshPortfolio"
        :disabled="loading"
        class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
      >
        {{ loading ? 'Loading...' : 'Refresh' }}
      </button>
    </div>
    
    <!-- Summary Cards -->
    <div class="grid md:grid-cols-3 gap-4 mb-8">
      <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
        <h3 class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Total Cost</h3>
        <p class="text-2xl font-bold">€{{ totalCost.toFixed(2) }}</p>
      </div>
      
      <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
        <h3 class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Total Value</h3>
        <p class="text-2xl font-bold">€{{ totalValue.toFixed(2) }}</p>
      </div>
      
      <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
        <h3 class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Gain/Loss</h3>
        <p class="text-2xl font-bold" :class="gainLossClass">
          €{{ totalGainLoss.toFixed(2) }}
        </p>
      </div>
    </div>
    
    <!-- Holdings Table -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <table class="w-full">
        <thead class="bg-gray-50 dark:bg-gray-700">
          <tr>
            <th class="px-4 py-3 text-left text-sm font-medium">Symbol</th>
            <th class="px-4 py-3 text-left text-sm font-medium">Name</th>
            <th class="px-4 py-3 text-right text-sm font-medium">Quantity</th>
            <th class="px-4 py-3 text-right text-sm font-medium">Purchase Price</th>
            <th class="px-4 py-3 text-right text-sm font-medium">Current Price</th>
            <th class="px-4 py-3 text-right text-sm font-medium">Value</th>
            <th class="px-4 py-3 text-right text-sm font-medium">Gain/Loss</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="holding in holdings" :key="holding.id" class="border-t dark:border-gray-700">
            <td class="px-4 py-3 text-sm">{{ holding.resolved_symbol || holding.symbol }}</td>
            <td class="px-4 py-3 text-sm">{{ holding.name }}</td>
            <td class="px-4 py-3 text-sm text-right">{{ holding.quantity }}</td>
            <td class="px-4 py-3 text-sm text-right">€{{ holding.purchase_price.toFixed(2) }}</td>
            <td class="px-4 py-3 text-sm text-right">
              €{{ (holding.current_price || holding.purchase_price).toFixed(2) }}
            </td>
            <td class="px-4 py-3 text-sm text-right">
              €{{ (holding.quantity * (holding.current_price || holding.purchase_price)).toFixed(2) }}
            </td>
            <td class="px-4 py-3 text-sm text-right" :class="getGainLossClass(holding)">
              €{{ getGainLoss(holding).toFixed(2) }}
            </td>
          </tr>
        </tbody>
      </table>
      
      <div v-if="!holdings || holdings.length === 0" class="p-8 text-center text-gray-500">
        No investments yet. Add your first investment to get started!
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { usePortfolioStore, type Investment } from '@/stores/portfolio'

const portfolioStore = usePortfolioStore()

const holdings = computed(() => portfolioStore.portfolio?.holdings || [])
const loading = computed(() => portfolioStore.loading)
const totalCost = computed(() => portfolioStore.totalCost)
const totalValue = computed(() => portfolioStore.totalValue)
const totalGainLoss = computed(() => portfolioStore.totalGainLoss)

const gainLossClass = computed(() => {
  return totalGainLoss.value >= 0 ? 'text-green-600' : 'text-red-600'
})

function getGainLoss(holding: Investment): number {
  const currentPrice = holding.current_price || holding.purchase_price
  return holding.quantity * (currentPrice - holding.purchase_price)
}

function getGainLossClass(holding: Investment): string {
  return getGainLoss(holding) >= 0 ? 'text-green-600' : 'text-red-600'
}

async function refreshPortfolio() {
  await portfolioStore.fetchPortfolio()
}

onMounted(() => {
  portfolioStore.fetchPortfolio()
})
</script>
