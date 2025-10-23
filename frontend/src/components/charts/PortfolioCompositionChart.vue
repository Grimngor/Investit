<template>
  <div class="portfolio-composition-chart" data-testid="portfolio-composition-chart">
    <h3 class="text-lg font-semibold mb-4">Portfolio Composition</h3>
    <div v-if="loading" class="flex justify-center items-center h-64">
      <LoadingSpinner />
    </div>
    <div v-else-if="error" class="text-center text-red-500 p-4">
      {{ error }}
    </div>
    <div v-else-if="hasData" class="chart-container">
      <Pie :data="chartData" :options="chartOptions" />
    </div>
    <div v-else class="text-center text-muted-foreground p-8">
      No investment data available. Add investments to see portfolio composition.
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Pie } from 'vue-chartjs'
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
  groupBy?: 'symbol' | 'type'
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  error: null,
  groupBy: 'symbol'
})

// Group investments by symbol or type
const compositionData = computed(() => {
  const holdings = portfolioStore.portfolio?.holdings || []
  if (holdings.length === 0) return {}

  const dataMap: Record<string, number> = {}

  holdings.forEach((investment: Investment) => {
    const key = props.groupBy === 'symbol' 
      ? investment.symbol 
      : (investment.asset_type || 'Other')
    
    const currentPrice = investment.current_price || investment.purchase_price
    const value = investment.quantity * currentPrice

    if (dataMap[key]) {
      dataMap[key] += value
    } else {
      dataMap[key] = value
    }
  })

  return dataMap
})

const hasData = computed(() => Object.keys(compositionData.value).length > 0)

// Chart data
const chartData = computed(() => {
  const data = compositionData.value
  const labels = Object.keys(data)
  const values = Object.values(data)

  // Generate colors based on number of items
  const colorPalette = [
    'rgba(59, 130, 246, 0.8)',   // blue
    'rgba(16, 185, 129, 0.8)',   // green
    'rgba(245, 158, 11, 0.8)',   // amber
    'rgba(239, 68, 68, 0.8)',    // red
    'rgba(139, 92, 246, 0.8)',   // purple
    'rgba(236, 72, 153, 0.8)',   // pink
    'rgba(14, 165, 233, 0.8)',   // sky
    'rgba(34, 197, 94, 0.8)',    // emerald
    'rgba(251, 191, 36, 0.8)',   // yellow
    'rgba(168, 85, 247, 0.8)',   // violet
    'rgba(249, 115, 22, 0.8)',   // orange
    'rgba(20, 184, 166, 0.8)',   // teal
  ]

  const borderPalette = colorPalette.map(color => color.replace('0.8', '1'))

  return {
    labels,
    datasets: [
      {
        label: 'Portfolio Value',
        data: values,
        backgroundColor: colorPalette,
        borderColor: borderPalette,
        borderWidth: 2
      }
    ]
  }
})

// Chart options
const chartOptions = computed<ChartOptions<'pie'>>(() => ({
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        padding: 15,
        font: {
          size: 12
        },
        generateLabels: (chart) => {
          const data = chart.data
          if (data.labels && data.datasets.length) {
            return data.labels.map((label, i) => {
              const value = data.datasets[0].data[i] as number
              const total = data.datasets[0].data.reduce((sum: number, val) => sum + (val as number), 0)
              const percentage = ((value / total) * 100).toFixed(1)
              const formattedValue = currencyStore.formatCurrency(value)
              
              return {
                text: `${label}: ${formattedValue} (${percentage}%)`,
                fillStyle: data.datasets[0].backgroundColor?.[i] as string,
                hidden: false,
                index: i,
                datasetIndex: 0
              }
            })
          }
          return []
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
.portfolio-composition-chart {
  @apply bg-card border border-border rounded-lg p-6 shadow-sm;
}

.chart-container {
  @apply max-w-2xl mx-auto;
}
</style>
