<template>
  <div>
        <div v-if="title" class="flex justify-between items-center mb-4">
          <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
            {{ title }}
            <span v-if="showCryptoBadge" class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300">
              Crypto {{ cryptoPctDisplay }}
            </span>
          </h3>
      <button
        v-if="type === 'geography' && canCollapseEU"
        @click="toggleEUCollapse"
        class="text-xs px-2 py-1 rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition"
      >
        {{ collapseEU ? 'Expand EU' : 'Collapse to Europe' }}
      </button>
    </div>

    <div class="chart-container">
      <Pie v-if="chartData" :data="chartData" :options="chartOptions" />
      <div v-else class="flex items-center justify-center h-48 text-gray-500 dark:text-gray-400">
        <p class="text-sm">No {{ type }} data available</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Pie } from 'vue-chartjs'
import {
	Chart as ChartJS,
	ArcElement,
	Tooltip,
	Legend,
	type ChartData,
	type ChartOptions,
} from 'chart.js'
import { useThemeStore } from '@/stores/theme'

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend)

const themeStore = useThemeStore()

interface AllocationData {
  [key: string]: number
}

interface Props {
  allocations?: AllocationData
  type?: 'instrument' | 'geography' | 'sector' | 'asset_type'
  title?: string
  loading?: boolean
  cryptoPct?: number // overall portfolio crypto percentage (0-100)
}

const props = withDefaults(defineProps<Props>(), {
  allocations: () => ({}),
  type: 'instrument',
  loading: false,
  cryptoPct: 0,
})

const showCryptoBadge = computed(() => props.type === 'asset_type' && props.cryptoPct > 0)
const cryptoPctDisplay = computed(() => `${props.cryptoPct.toFixed(1)}%`)

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
const chartData = computed<ChartData<'pie'> | null>(() => {
  const data = processedAllocations.value
  if (!data || Object.keys(data).length === 0) {
    return null
  }

  const labels = Object.keys(data)
  const values = Object.values(data)

  // Calculate total for percentage calculation
  const total = values.reduce((sum, val) => sum + val, 0)

  const backgroundColors = labels.map((_, index) => colorPalette[index % colorPalette.length])

  return {
    labels,
    datasets: [
      {
        data: values,
        backgroundColor: backgroundColors,
        borderWidth: 2,
        borderColor: document.documentElement.classList.contains('dark') ? '#1f2937' : '#ffffff',
        // Store total for percentage calculation in tooltip
        total: total,
      },
    ],
  }
})

// Chart options with dark mode support
const chartOptions = computed<ChartOptions<'pie'>>(() => {
  const textColor = themeStore.isDark ? '#f3f4f6' : '#374151' // gray-100 for dark, gray-700 for light

  return {
    responsive: true,
    maintainAspectRatio: false,
    layout: {
      padding: {
        right: 0,
        left: 20,
        top: 0,
        bottom: 0
      }
    },
    plugins: {
      legend: {
        display: true,
        position: 'right',
        align: 'center',
        maxWidth: 200,
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
              const total = (data.datasets[0].data as number[]).reduce((sum, val) => sum + val, 0)
              return data.labels.map((label, i) => {
                const value = data.datasets[0].data[i] as number
                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0'
                const bgColors = data.datasets[0].backgroundColor as string[]
                return {
                  text: `${label}: ${percentage}%`,
                  fillStyle: bgColors[i],
                  fontColor: textColor,
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
        backgroundColor: themeStore.isDark ? '#1f2937' : '#ffffff',
        titleColor: textColor,
        bodyColor: textColor,
        borderColor: themeStore.isDark ? '#374151' : '#e5e7eb',
        borderWidth: 1,
        padding: 12,
        callbacks: {
          label: function (context) {
            const label = context.label || ''
            const value = context.parsed as number
            const total = (context.dataset.data as number[]).reduce((sum: number, val: number) => sum + val, 0)
            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0'
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
	height: 340px; /* enlarged height */
	width: 100%;
}
</style>
