<template>
  <div class="max-w-7xl mx-auto px-6 py-10">
    <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-8">
      <div>
        <h1 class="page-title">Dashboard</h1>
        <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">High-level overview & KPIs</p>
      </div>
    </div>

    <!-- KPI Cards -->
    <div class="grid gap-4 md:grid-cols-3 mb-10">
      <SummaryCard label="Total Cost" :value="totalCost" prefix="€" />
      <SummaryCard label="Total Value" :value="totalValue" prefix="€" />
      <SummaryCard label="Gain/Loss" :value="totalGainLoss" prefix="€" :value-class="gainLossClass" />
    </div>

    <!-- Placeholder charts area -->
    <div class="rounded-xl border border-softblue-200 dark:border-gray-700 bg-white dark:bg-gray-800/60 backdrop-blur p-6 shadow-sm">
      <h2 class="text-lg font-semibold mb-4 text-gray-800 dark:text-gray-200">Performance (Coming Soon)</h2>
      <div class="grid md:grid-cols-2 gap-6">
        <div class="h-56 flex items-center justify-center border border-dashed border-softblue-300 dark:border-gray-600 rounded-md text-xs text-gray-500 dark:text-gray-400">
          Chart placeholder
        </div>
        <div class="h-56 flex items-center justify-center border border-dashed border-softblue-300 dark:border-gray-600 rounded-md text-xs text-gray-500 dark:text-gray-400">
          Allocation placeholder
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { usePortfolioStore } from '@/stores/portfolio'
import SummaryCard from '@/components/SummaryCard.vue'

const portfolioStore = usePortfolioStore()

const totalCost = computed(() => portfolioStore.totalCost)
const totalValue = computed(() => portfolioStore.totalValue)
const totalGainLoss = computed(() => portfolioStore.totalGainLoss)
const gainLossClass = computed(() => (totalGainLoss.value >= 0 ? 'text-green-600' : 'text-red-600'))
</script>

<style scoped></style>
