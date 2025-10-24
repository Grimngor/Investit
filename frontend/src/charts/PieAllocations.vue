<template>
  <div class="chart-container">
    <div v-if="title" class="flex justify-between items-center mb-4">
      <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">{{ title }}</h3>
      <button
        v-if="type === 'geography' && canCollapseEU"
        @click="toggleEUCollapse"
        class="text-xs px-2 py-1 rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition"
      >
        {{ collapseEU ? 'Expand EU' : 'Collapse to Europe' }}
      </button>
    </div>

    <Doughnut v-if="chartData" :data="chartData" :options="chartOptions" />
    <div v-else class="flex items-center justify-center h-48 text-gray-500 dark:text-gray-400">
      <p class="text-sm">No {{ type }} data available</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  type ChartData,
  type ChartOptions,
} from 'chart.js'

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend)

interface AllocationData {
  [key: string]: number
}

interface Props {
  allocations?: AllocationData
  type?: 'instrument' | 'geography' | 'sector' | 'asset_type'
  title?: string
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  allocations: () => ({}),
  type: 'instrument',
  loading: false,
})

const collapseEU = ref(false)

// EU country codes for geography collapse feature
const EU_COUNTRIES = [
  'AT',
  'BE',
  'BG',
  'HR',
  'CY',
  'CZ',
  'DK',
  'EE',
  'FI',
  'FR',
  'DE',
  'GR',
  'HU',
  'IE',
  'IT',
  'LV',
  'LT',
  'LU',
  'MT',
  'NL',
  'PL',
  'PT',
  'RO',
  'SK',
  'SI',
  'ES',
  'SE',
]

// Check if data contains EU countries that can be collapsed
const canCollapseEU = computed(() => {
  if (props.type !== 'geography' || !props.allocations) return false
  const keys = Object.keys(props.allocations)
  return keys.some((key) => EU_COUNTRIES.includes(key.toUpperCase()))
})

// Process allocations (collapse EU if enabled)
const processedAllocations = computed<AllocationData>(() => {
  if (!props.allocations) return {}

  if (props.type === 'geography' && collapseEU.value) {
    const result: AllocationData = {}
    let europeTotal = 0

    for (const [key, value] of Object.entries(props.allocations)) {
      if (EU_COUNTRIES.includes(key.toUpperCase())) {
        europeTotal += value
      } else {
        result[key] = value
      }
    }

    if (europeTotal > 0) {
      result['Europe'] = europeTotal
    }

    return result
  }

  return props.allocations
})

// Color palette optimized for dark/light mode
const colorPalette = [
  'rgb(59, 130, 246)', // blue-500
  'rgb(16, 185, 129)', // green-500
  'rgb(245, 158, 11)', // amber-500
  'rgb(239, 68, 68)', // red-500
  'rgb(139, 92, 246)', // violet-500
  'rgb(236, 72, 153)', // pink-500
  'rgb(20, 184, 166)', // teal-500
  'rgb(251, 146, 60)', // orange-500
  'rgb(99, 102, 241)', // indigo-500
  'rgb(244, 63, 94)', // rose-500
  'rgb(14, 165, 233)', // sky-500
  'rgb(168, 85, 247)', // purple-500
]

// Generate chart data
const chartData = computed<ChartData<'doughnut'> | null>(() => {
  const data = processedAllocations.value
  if (!data || Object.keys(data).length === 0) {
    return null
  }

  const labels = Object.keys(data)
  const values = Object.values(data)
  const backgroundColors = labels.map((_, index) => colorPalette[index % colorPalette.length])

  return {
    labels,
    datasets: [
      {
        data: values,
        backgroundColor: backgroundColors,
        borderWidth: 2,
        borderColor: document.documentElement.classList.contains('dark') ? '#1f2937' : '#ffffff',
      },
    ],
  }
})

// Chart options with dark mode support
const chartOptions = computed<ChartOptions<'doughnut'>>(() => {
  const isDark = document.documentElement.classList.contains('dark')
  const textColor = isDark ? '#d1d5db' : '#374151'

  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'right',
        labels: {
          color: textColor,
          font: {
            size: 11,
            family: "'Inter', sans-serif",
          },
          padding: 10,
          usePointStyle: true,
          generateLabels: function (chart) {
            const data = chart.data
            if (data.labels && data.datasets.length) {
              return data.labels.map((label, i) => {
                const value = data.datasets[0].data[i] as number
                const percentage = (value * 100).toFixed(1)
                const bgColors = data.datasets[0].backgroundColor as string[]
                return {
                  text: `${label}: ${percentage}%`,
                  fillStyle: bgColors[i],
                  hidden: false,
                  index: i,
                }
              })
            }
            return []
          },
        },
      },
      tooltip: {
        backgroundColor: isDark ? '#1f2937' : '#ffffff',
        titleColor: textColor,
        bodyColor: textColor,
        borderColor: isDark ? '#374151' : '#e5e7eb',
        borderWidth: 1,
        padding: 12,
        callbacks: {
          label: function (context) {
            const label = context.label || ''
            const value = context.parsed as number
            const percentage = (value * 100).toFixed(1)
            return `${label}: ${percentage}%`
          },
        },
      },
    },
  }
})

function toggleEUCollapse() {
  collapseEU.value = !collapseEU.value
}
</script>

<style scoped>
.chart-container {
  position: relative;
  height: 280px;
  width: 100%;
}
</style>
