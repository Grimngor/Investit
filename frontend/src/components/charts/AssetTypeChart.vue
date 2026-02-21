<template>
  <div class="asset-type-chart">
    <h3 class="text-lg font-semibold mb-4">Portfolio Allocation by Asset Type</h3>
    <div v-if="loading" class="flex justify-center items-center h-64">
      <LoadingSpinner />
    </div>
    <div v-else-if="error" class="text-center text-red-500 p-4">
      {{ error }}
    </div>
    <div v-else-if="hasData" class="chart-container h-72 w-full max-w-[400px] mx-auto">
      <Doughnut :data="chartData" :options="chartOptions" />
    </div>
    <div v-else class="text-center text-muted-foreground p-8">
      No investment data available. Add investments to see portfolio allocation.
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js'
import type { ChartOptions } from 'chart.js'
import { usePortfolioStore, type Investment } from '@/stores/portfolio'
import { useCurrencyStore } from '@/stores/currency'
import LoadingSpinner from '../LoadingSpinner.vue'

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend)

const portfolioStore = usePortfolioStore()
const currencyStore = useCurrencyStore()

interface Props {
  loading?: boolean
  error?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  error: null
})

// Group investments by asset type and calculate total value
const assetTypeData = computed(() => {
  const holdings = portfolioStore.portfolio?.holdings || []
  if (holdings.length === 0) return {}

  const typeMap: Record<string, number> = {}

  holdings.forEach((investment: Investment) => {
    const type = investment.asset_type || 'Other'
    const currentPrice = investment.current_price || investment.purchase_price
    const value = investment.quantity * currentPrice

    if (typeMap[type]) {
      typeMap[type] += value
    } else {
      typeMap[type] = value
    }
  })

  return typeMap
})

const hasData = computed(() => Object.keys(assetTypeData.value).length > 0)

// Chart data
const chartData = computed(() => {
  const data = assetTypeData.value
  const labels = Object.keys(data)
  const values = Object.values(data)

  return {
    labels,
    datasets: [
      {
        label: 'Asset Allocation',
        data: values,
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',   // blue
          'rgba(16, 185, 129, 0.8)',   // green
          'rgba(245, 158, 11, 0.8)',   // amber
          'rgba(239, 68, 68, 0.8)',    // red
          'rgba(139, 92, 246, 0.8)',   // purple
          'rgba(236, 72, 153, 0.8)',   // pink
          'rgba(14, 165, 233, 0.8)',   // sky
          'rgba(34, 197, 94, 0.8)',    // emerald
        ],
        borderColor: [
          'rgba(59, 130, 246, 1)',
          'rgba(16, 185, 129, 1)',
          'rgba(245, 158, 11, 1)',
          'rgba(239, 68, 68, 1)',
          'rgba(139, 92, 246, 1)',
          'rgba(236, 72, 153, 1)',
          'rgba(14, 165, 233, 1)',
          'rgba(34, 197, 94, 1)',
        ],
        borderWidth: 2
      }
    ]
  }
})

// Chart options
const chartOptions = computed<ChartOptions<'doughnut'>>(() => ({
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        padding: 15,
        font: {
          size: 12
        }
      }
    },
    tooltip: {
      callbacks: {
        label: (context) => {
          const label = context.label || ''
          const value = context.parsed || 0
          const total = context.dataset.data.reduce((sum: number, val) => sum + (val as number), 0)
          const percentage = ((value / total) * 100).toFixed(1)
          const formattedValue = currencyStore.formatCurrency(value)
          return `${label}: ${formattedValue} (${percentage}%)`
        }
      }
    }
  }
}))
</script>

<style scoped>
.asset-type-chart {
  @apply bg-card border border-border rounded-lg p-6 shadow-sm;
}

.chart-container {
  position: relative;
  height: 340px;
  width: 100%;
}
</style>
