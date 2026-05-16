<template>
  <div class="w-full mx-auto px-6 py-10 max-w-[1600px]">
    <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-8">
      <div>
        <h1 class="page-title">Dashboard</h1>
        <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">High-level overview & KPIs</p>
      </div>

      <div
        v-if="refreshingPrices"
        class="flex items-center gap-2 px-3 py-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg"
      >
        <span class="h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
        <span class="text-sm font-medium text-blue-800 dark:text-blue-200">
          Refreshing prices...
        </span>
      </div>

      <!-- Stale Price Warning -->
      <div
        v-else-if="hasStaleData"
        class="flex items-center gap-2 px-3 py-2 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg"
      >
        <svg
          class="w-5 h-5 text-amber-600 dark:text-amber-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        <span class="text-sm font-medium text-amber-800 dark:text-amber-200">
          {{ staleCount }} instrument{{ staleCount > 1 ? 's' : '' }} with stale prices (>3 days)
        </span>
      </div>
    </div>

    <!-- KPI Cards -->
    <div class="grid gap-4 md:grid-cols-3 mb-10">
      <SummaryCard label="Total Invested" :value="totalCost" suffix="€" />
      <SummaryCard label="Current Value" :value="totalValue" suffix="€" />
      <SummaryCard
        label="Gain / Loss"
        :value="totalGainLoss"
        suffix="€"
        :value-class="gainLossClass"
        :show-sign="true"
        :percentage="gainLossPercentageNum"
      />
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="text-gray-500 dark:text-gray-400">Loading dashboard data...</div>
    </div>

    <!-- Performance Chart -->
    <div v-else class="space-y-6">
      <div
        class="rounded-xl border border-softblue-200 dark:border-gray-700 bg-white dark:bg-gray-800/60 backdrop-blur p-6 shadow-sm"
      >
        <h2 class="text-lg font-semibold mb-6 text-gray-800 dark:text-gray-200">
          Portfolio Performance
        </h2>
        <LineInvestedVsCurrent :time-series="timeSeries" :loading="loading" />
      </div>

      <!-- Allocation Charts -->
      <div
        class="rounded-xl border border-softblue-200 dark:border-gray-700 bg-white dark:bg-gray-800/60 backdrop-blur p-6 shadow-sm"
      >
        <div class="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200">
            Asset Allocation
          </h2>
          <button
            type="button"
            class="inline-flex items-center justify-center rounded-md border px-3 py-1.5 text-sm font-medium transition"
            :class="
              showAllocationLegends
                ? 'border-blue-600 bg-blue-600 text-white'
                : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700'
            "
            :aria-pressed="showAllocationLegends"
            @click="toggleAllocationLegends"
          >
            Legends
          </button>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
          <PieAllocations
            :allocations="allocations?.by_instrument"
            type="instrument"
            title="By Fund"
            :loading="loading"
            :show-legend="showAllocationLegends"
          />
          <PieAllocations
            :allocations="allocations?.by_geography"
            type="geography"
            title="By Geography"
            :loading="loading"
            :show-legend="showAllocationLegends"
          />
          <PieAllocations
            :allocations="allocations?.by_sector"
            type="sector"
            title="By Sector"
            :loading="loading"
            :show-legend="showAllocationLegends"
          />
          <PieAllocations
            :allocations="allocations?.by_asset_type"
            type="asset_type"
            title="By Asset Type"
            :loading="loading"
            :show-legend="showAllocationLegends"
          />
        </div>
      </div>

      <!-- Stale Instruments Details (if any) -->
      <div
        v-if="hasStaleData && staleInstruments.length > 0"
        class="rounded-xl border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/10 p-6 shadow-sm"
      >
        <h3 class="text-base font-semibold mb-4 text-amber-900 dark:text-amber-200">
          Stale Price Details
        </h3>
        <div class="space-y-2">
          <div
            v-for="instrument in staleInstruments"
            :key="instrument.isin"
            class="flex items-center justify-between text-sm"
          >
            <div>
              <span class="font-medium text-amber-900 dark:text-amber-200">{{
                instrument.name
              }}</span>
              <span class="text-amber-700 dark:text-amber-400 ml-2">({{ instrument.symbol }})</span>
            </div>
            <div class="text-amber-700 dark:text-amber-400">
              Last updated: {{ instrument.last_price_date }} ({{ instrument.days_stale }} days ago)
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { usePortfolioStore } from '@/stores/portfolio'
import { useDashboardStore } from '@/stores/dashboard'
import { wsClient } from '@/services/websocket'
import SummaryCard from '@/components/SummaryCard.vue'
import LineInvestedVsCurrent from '@/charts/LineInvestedVsCurrent.vue'
import PieAllocations from '@/charts/PieAllocations.vue'

const portfolioStore = usePortfolioStore()
const dashboardStore = useDashboardStore()
const isDesktop = ref(currentDesktopState())
const allocationLegendPreference = ref<boolean | null>(null)
const showAllocationLegends = computed(() => allocationLegendPreference.value ?? isDesktop.value)

const totalCost = computed(() => portfolioStore.totalCost)
const totalValue = computed(() => portfolioStore.totalValue)
const totalGainLoss = computed(() => portfolioStore.totalGainLoss)
const gainLossClass = computed(() => (totalGainLoss.value >= 0 ? 'text-green-600' : 'text-red-600'))

// Percentage gain/loss relative to total invested (as number for component prop)
const gainLossPercentageNum = computed(() => {
  const invested = totalCost.value || 0
  if (!invested || invested === 0) return 0
  return (totalGainLoss.value / invested) * 100
})

const loading = computed(() => dashboardStore.loading)
const timeSeries = computed(() => dashboardStore.timeSeries)
const allocations = computed(() => dashboardStore.allocations)
const hasStaleData = computed(() => dashboardStore.hasStaleData)
const staleCount = computed(() => dashboardStore.priceStatus?.stale_count || 0)
const staleInstruments = computed(() => dashboardStore.staleInstruments)
const refreshingPrices = computed(() => dashboardStore.refreshingPrices)

async function handlePricesUpdated() {
  await Promise.all([dashboardStore.handlePricesUpdated(), portfolioStore.fetchPortfolio()])
}

function currentDesktopState(): boolean {
  if (typeof window === 'undefined' || !window.matchMedia) return false
  return window.matchMedia('(min-width: 1024px)').matches
}

function syncDesktopState() {
  isDesktop.value = currentDesktopState()
}

function toggleAllocationLegends() {
  allocationLegendPreference.value = !showAllocationLegends.value
}

onMounted(async () => {
  syncDesktopState()
  window.addEventListener('resize', syncDesktopState)
  wsClient.on('prices_updated', handlePricesUpdated)
  await Promise.all([portfolioStore.fetchPortfolio(), dashboardStore.fetchAll()])
  await dashboardStore.refreshPricesIfNeeded()
})

onUnmounted(() => {
  window.removeEventListener('resize', syncDesktopState)
  wsClient.off('prices_updated', handlePricesUpdated)
})
</script>

<style scoped></style>
