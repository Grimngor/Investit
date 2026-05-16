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
  const isoDate = value.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (isoDate) {
    const [, year, month, day] = isoDate
    const parsed = new Date(Number(year), Number(month) - 1, Number(day))
    return Number.isNaN(parsed.getTime()) ? null : parsed
  }

  const ddmmyyyy = value.match(/^(\d{2})[/-](\d{2})[/-](\d{2}|\d{4})$/)
  if (ddmmyyyy) {
    const [, day, month, year] = ddmmyyyy
    const fullYear = year.length === 2 ? `20${year}` : year
    const parsed = new Date(Number(fullYear), Number(month) - 1, Number(day))
    return Number.isNaN(parsed.getTime()) ? null : parsed
  }

  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

function formatDateKey(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function clonePointAtDate(point: TimeSeriesDataPoint, date: Date): TimeSeriesDataPoint {
  return {
    ...point,
    date: formatDateKey(date),
  }
}

function sortedTimeSeries(): TimeSeriesDataPoint[] {
  return [...props.timeSeries].sort((a, b) => {
    const dateA = parsePointDate(a.date)?.getTime() ?? 0
    const dateB = parsePointDate(b.date)?.getTime() ?? 0
    return dateA - dateB
  })
}

function rangeStartDate(anchorDate: Date, months: number): Date {
  const startDate = new Date(anchorDate)
  startDate.setMonth(startDate.getMonth() - months)
  return startDate
}

function windowTimeSeries(points: TimeSeriesDataPoint[], months: number): TimeSeriesDataPoint[] {
  const latestDate = parsePointDate(points[points.length - 1]?.date || '')
  if (!latestDate) {
    return points
  }

  const startDate = rangeStartDate(latestDate, months)
  const insideWindow: TimeSeriesDataPoint[] = []
  let previousPoint: TimeSeriesDataPoint | null = null

  for (const point of points) {
    const parsed = parsePointDate(point.date)

    if (!parsed || parsed >= startDate) {
      insideWindow.push(point)
    } else {
      previousPoint = point
    }
  }

  if (previousPoint) {
    insideWindow.unshift(clonePointAtDate(previousPoint, startDate))
  }

  return insideWindow.length > 0 ? insideWindow : points.slice(-1)
}

function selectedRangeMonths(): number | null {
  const range = ranges.find((item) => item.value === selectedRange.value)
  return range?.months ?? null
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
  const sortedPoints = sortedTimeSeries()
  const months = selectedRangeMonths()

  if (!months || sortedPoints.length === 0) {
    return sortedPoints
  }

  const windowedPoints = windowTimeSeries(sortedPoints, months)
  return windowedPoints
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
