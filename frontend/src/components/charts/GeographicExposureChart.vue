<template>
  <div class="geographic-exposure-chart">
    <h3 class="text-lg font-semibold mb-4">Geographic Exposure</h3>
    <div v-if="loading" class="flex justify-center items-center h-64">
      <LoadingSpinner />
    </div>
    <div v-else-if="error" class="text-center text-red-500 p-4">
      {{ error }}
    </div>
    <div v-else-if="hasData" class="chart-container h-72 w-full max-w-[400px] mx-auto">
      <Pie :data="chartData" :options="chartOptions" />
      <div class="mt-4 text-sm text-muted-foreground text-center">
        Based on fund holdings and company headquarters
      </div>
    </div>
    <div v-else class="text-center text-muted-foreground p-8">
      No geographic exposure data available. Add ETFs or Index Funds with ISIN codes to see geographic breakdown.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Pie } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js'
import type { ChartOptions } from 'chart.js'
import { apiClient } from '@/services/api'
import { useCurrencyStore } from '@/stores/currency'
import { useThemeStore } from '@/stores/theme'
import LoadingSpinner from '../LoadingSpinner.vue'

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend)

const themeStore = useThemeStore()

const currencyStore = useCurrencyStore()

interface GeographicExposure {
  exposure: Record<string, number>
  total_value: number
}

interface Props {
  autoLoad?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  autoLoad: true
})

const loading = ref(false)
const error = ref<string | null>(null)
const exposureData = ref<GeographicExposure | null>(null)

const hasData = computed(() => {
  return exposureData.value && Object.keys(exposureData.value.exposure).length > 0
})

// Chart data
const chartData = computed(() => {
  if (!exposureData.value) {
    return { labels: [], datasets: [] }
  }

  const { exposure } = exposureData.value
  const labels = Object.keys(exposure)
  const values = Object.values(exposure)

  return {
    labels,
    datasets: [
      {
        label: 'Geographic Allocation (%)',
        data: values,
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',   // blue - US
          'rgba(16, 185, 129, 0.8)',   // green - Europe
          'rgba(245, 158, 11, 0.8)',   // amber - Asia
          'rgba(239, 68, 68, 0.8)',    // red - Emerging
          'rgba(139, 92, 246, 0.8)',   // purple - Other
          'rgba(236, 72, 153, 0.8)',   // pink
          'rgba(14, 165, 233, 0.8)',   // sky
          'rgba(34, 197, 94, 0.8)',    // emerald
          'rgba(251, 191, 36, 0.8)',   // yellow
          'rgba(168, 85, 247, 0.8)',   // violet
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
          'rgba(251, 191, 36, 1)',
          'rgba(168, 85, 247, 1)',
        ],
        borderWidth: 2
      }
    ]
  }
})

// Chart options
const chartOptions = computed<ChartOptions<'pie'>>(() => {
  const textColor = themeStore.isDark ? '#f3f4f6' : '#374151' // gray-100 for dark, gray-700 for light

  return {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: 'right',
        labels: {
          color: textColor,
          padding: 10,
          font: {
            size: 11
          },
          generateLabels: (chart) => {
            const data = chart.data
            if (data.labels && data.datasets.length) {
              return data.labels.map((label, i) => {
                const value = data.datasets[0].data[i] as number
                const bgColors = data.datasets[0].backgroundColor as string[]
                return {
                  text: `${label}: ${value.toFixed(1)}%`,
                  fillStyle: bgColors[i],
                  fontColor: textColor,
                  hidden: false,
                  index: i
                }
              })
            }
            return []
          }
        }
      },
      tooltip: {
        backgroundColor: themeStore.isDark ? '#1f2937' : '#ffffff',
        titleColor: textColor,
        bodyColor: textColor,
        borderColor: themeStore.isDark ? '#374151' : '#e5e7eb',
        borderWidth: 1,
        callbacks: {
          label: (context) => {
            const label = context.label || ''
            const value = context.parsed || 0
            return `${label}: ${value.toFixed(2)}%`
          }
        }
      }
    }
  }
})

async function loadGeographicExposure() {
  loading.value = true
  error.value = null

  try {
    exposureData.value = await apiClient.getGeographicExposure()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load geographic exposure'
    console.error('Geographic exposure error:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (props.autoLoad) {
    loadGeographicExposure()
  }
})

defineExpose({
  loadGeographicExposure
})
</script>

<style scoped>
.geographic-exposure-chart {
  @apply bg-card border border-border rounded-lg p-6 shadow-sm;
}

.chart-container {
  position: relative;
  height: 340px;
  width: 100%;
}
</style>
