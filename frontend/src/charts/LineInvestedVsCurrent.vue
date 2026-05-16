<template>
  <div>
    <div class="chart-container">
      <Line v-if="chartData" :data="chartData" :options="chartOptions" />
      <div v-else class="flex h-64 items-center justify-center text-gray-500 dark:text-gray-400">
        <p>No data available</p>
      </div>
    </div>

    <div
      v-if="props.timeSeries.length > 0"
      class="mt-4 flex flex-wrap items-center justify-center gap-2"
      aria-label="Portfolio performance time range"
    >
      <button
        v-for="range in ranges"
        :key="range.value"
        type="button"
        class="min-w-12 rounded-md border px-3 py-1.5 text-sm font-medium transition"
        :class="
          selectedRange === range.value
            ? 'border-blue-600 bg-blue-600 text-white'
            : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700'
        "
        @click="selectedRange = range.value"
      >
        {{ range.label }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Line } from 'vue-chartjs'
import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
  type ChartData,
  type ChartOptions,
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
)

interface TimeSeriesDataPoint {
  date: string
  invested_value: number
  current_value: number
}

interface Props {
  timeSeries?: TimeSeriesDataPoint[]
  loading?: boolean
}

type RangeValue = '1M' | '3M' | '6M' | '1Y' | '3Y' | 'MAX'

const props = withDefaults(defineProps<Props>(), {
  timeSeries: () => [],
  loading: false,
})

const ranges: Array<{ label: string; value: RangeValue; months?: number }> = [
  { label: '1M', value: '1M', months: 1 },
  { label: '3M', value: '3M', months: 3 },
  { label: '6M', value: '6M', months: 6 },
  { label: '1Y', value: '1Y', months: 12 },
  { label: '3Y', value: '3Y', months: 36 },
  { label: 'Max', value: 'MAX' },
]

const selectedRange = ref<RangeValue>('MAX')

function parsePointDate(value: string): Date | null {
  const parsed = new Date(value)
  if (!Number.isNaN(parsed.getTime())) {
    return parsed
  }

  const ddmmyyyy = value.match(/^(\d{2})\/(\d{2})\/(\d{2}|\d{4})$/)
  if (!ddmmyyyy) {
    return null
  }

  const [, day, month, year] = ddmmyyyy
  const fullYear = year.length === 2 ? `20${year}` : year
  const fallback = new Date(`${fullYear}-${month}-${day}`)
  return Number.isNaN(fallback.getTime()) ? null : fallback
}

function formatShortDate(value: string): string {
  const parsed = parsePointDate(value)
  if (!parsed) {
    return value
  }

  const day = String(parsed.getDate()).padStart(2, '0')
  const month = String(parsed.getMonth() + 1).padStart(2, '0')
  const year = String(parsed.getFullYear()).slice(-2)
  return `${day}/${month}/${year}`
}

const filteredTimeSeries = computed(() => {
  if (selectedRange.value === 'MAX' || props.timeSeries.length === 0) {
    return props.timeSeries
  }

  const latestDate = props.timeSeries.reduce<Date | null>((latest, point) => {
    const parsed = parsePointDate(point.date)
    if (!parsed) return latest
    return !latest || parsed > latest ? parsed : latest
  }, null)
  const range = ranges.find((item) => item.value === selectedRange.value)

  if (!latestDate || !range?.months) {
    return props.timeSeries
  }

  const startDate = new Date(latestDate)
  startDate.setMonth(startDate.getMonth() - range.months)

  return props.timeSeries.filter((point) => {
    const parsed = parsePointDate(point.date)
    return parsed ? parsed >= startDate : true
  })
})

const chartData = computed<ChartData<'line'> | null>(() => {
  if (filteredTimeSeries.value.length === 0) {
    return null
  }

  const labels = filteredTimeSeries.value.map((point) => formatShortDate(point.date))
  const investedValues = filteredTimeSeries.value.map((point) => point.invested_value)
  const currentValues = filteredTimeSeries.value.map((point) => point.current_value)

  return {
    labels,
    datasets: [
      {
        label: 'Invested Value',
        data: investedValues,
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5,
        tension: 0.2,
        fill: true,
      },
      {
        label: 'Current Value',
        data: currentValues,
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        borderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5,
        tension: 0.2,
        fill: true,
      },
    ],
  }
})

const chartOptions = computed<ChartOptions<'line'>>(() => {
  const isDark = document.documentElement.classList.contains('dark')
  const textColor = isDark ? '#d1d5db' : '#374151'
  const gridColor = isDark ? '#374151' : '#e5e7eb'

  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          color: textColor,
          font: {
            size: 12,
            family: "'Inter', sans-serif",
          },
          usePointStyle: true,
          padding: 15,
        },
      },
      tooltip: {
        backgroundColor: isDark ? '#1f2937' : '#ffffff',
        titleColor: textColor,
        bodyColor: textColor,
        borderColor: gridColor,
        borderWidth: 1,
        padding: 12,
        displayColors: true,
        callbacks: {
          title: (context) => context[0]?.label || '',
          label: (context) => {
            let label = context.dataset.label || ''
            if (label) {
              label += ': '
            }
            if (context.parsed.y !== null) {
              label += `€${context.parsed.y.toFixed(2)}`
            }
            return label
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          color: gridColor,
          display: false,
        },
        ticks: {
          color: textColor,
          font: {
            size: 11,
          },
          maxRotation: 45,
          minRotation: 0,
        },
      },
      y: {
        grid: {
          color: gridColor,
        },
        ticks: {
          color: textColor,
          font: {
            size: 11,
          },
          callback: (value) => `€${Number(value).toFixed(0)}`,
        },
        beginAtZero: true,
      },
    },
  }
})
</script>

<style scoped>
.chart-container {
  position: relative;
  height: 320px;
  width: 100%;
}
</style>
