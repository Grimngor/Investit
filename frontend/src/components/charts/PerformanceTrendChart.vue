<template>
  <div class="performance-trend-chart">
    <h3 class="text-lg font-semibold mb-4">Performance Trend</h3>
    <div v-if="loading" class="flex justify-center items-center h-64">
      <LoadingSpinner />
    </div>
    <div v-else-if="error" class="text-center text-red-500 p-4">
      {{ error }}
    </div>
    <div v-else-if="hasData" class="chart-container">
      <Line :data="chartData" :options="chartOptions" />
      <div class="flex justify-center gap-4 mt-4">
        <button
          v-for="period in timePeriods"
          :key="period.value"
          @click="selectedPeriod = period.value"
          :class="[
            'px-4 py-2 rounded-md text-sm font-medium transition-colors',
            selectedPeriod === period.value
              ? 'bg-primary text-primary-foreground'
              : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
          ]"
        >
          {{ period.label }}
        </button>
      </div>
    </div>
    <div v-else class="text-center text-muted-foreground p-8">
      No performance data available. Portfolio values will be tracked over time.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import type { ChartOptions } from 'chart.js'
import { usePortfolioStore, type Investment } from '@/stores/portfolio'
import { useCurrencyStore } from '@/stores/currency'
import LoadingSpinner from '../LoadingSpinner.vue'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

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

const timePeriods = [
  { label: '1W', value: 7 },
  { label: '1M', value: 30 },
  { label: '3M', value: 90 },
  { label: '1Y', value: 365 },
  { label: 'All', value: 0 }
]

const selectedPeriod = ref(30) // Default 1 month

// Generate historical performance data (simulated for now)
// In a real app, this would come from stored historical snapshots
const performanceData = computed(() => {
  const holdings = portfolioStore.portfolio?.holdings || []
  if (holdings.length === 0) return { dates: [], values: [] }

  const today = new Date()
  const days = selectedPeriod.value || 365
  const dates: string[] = []
  const values: number[] = []

  // Calculate current total value
  const currentValue = holdings.reduce((sum, inv: Investment) => {
    const price = inv.current_price || inv.purchase_price
    return sum + inv.quantity * price
  }, 0)

  // Calculate total cost
  const totalCost = holdings.reduce((sum, inv: Investment) => {
    return sum + inv.quantity * inv.purchase_price
  }, 0)

  // Generate historical data points (simulated growth from purchase to current)
  for (let i = days; i >= 0; i -= Math.max(1, Math.floor(days / 30))) {
    const date = new Date(today)
    date.setDate(date.getDate() - i)
    dates.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }))

    // Linear interpolation between cost and current value
    const progress = (days - i) / days
    const value = totalCost + (currentValue - totalCost) * progress
    values.push(value)
  }

  // Add today's value
  dates.push(today.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }))
  values.push(currentValue)

  return { dates, values }
})

const hasData = computed(() => performanceData.value.dates.length > 0)

// Chart data
const chartData = computed(() => {
  const { dates, values } = performanceData.value

  return {
    labels: dates,
    datasets: [
      {
        label: 'Portfolio Value',
        data: values,
        borderColor: 'rgba(59, 130, 246, 1)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 5,
        pointBackgroundColor: 'rgba(59, 130, 246, 1)',
        pointBorderColor: '#fff',
        pointBorderWidth: 2
      }
    ]
  }
})

// Chart options
const chartOptions = computed<ChartOptions<'line'>>(() => ({
  responsive: true,
  maintainAspectRatio: true,
  interaction: {
    mode: 'index',
    intersect: false
  },
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      callbacks: {
        label: (context) => {
          const value = context.parsed.y || 0
          const formattedValue = currencyStore.formatCurrency(value)
          return `Value: ${formattedValue}`
        }
      }
    }
  },
  scales: {
    x: {
      grid: {
        display: false
      }
    },
    y: {
      beginAtZero: false,
      ticks: {
        callback: (value) => {
          return currencyStore.formatCurrency(value as number)
        }
      }
    }
  }
}))
</script>

<style scoped>
.performance-trend-chart {
  @apply bg-card border border-border rounded-lg p-6 shadow-sm;
}

.chart-container {
  @apply w-full;
}
</style>
