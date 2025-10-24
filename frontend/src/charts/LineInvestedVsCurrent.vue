<template>
  <div class="chart-container">
    <Line v-if="chartData" :data="chartData" :options="chartOptions" />
    <div v-else class="flex items-center justify-center h-64 text-gray-500 dark:text-gray-400">
      <p>No data available</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
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
  Filler,
  type ChartData,
  type ChartOptions,
} from 'chart.js'

// Register Chart.js components
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

const props = withDefaults(defineProps<Props>(), {
  timeSeries: () => [],
  loading: false,
})

// Extract data for chart
const chartData = computed<ChartData<'line'> | null>(() => {
  if (!props.timeSeries || props.timeSeries.length === 0) {
    return null
  }

  const labels = props.timeSeries.map((point) => point.date)
  const investedValues = props.timeSeries.map((point) => point.invested_value)
  const currentValues = props.timeSeries.map((point) => point.current_value)

  return {
    labels,
    datasets: [
      {
        label: 'Invested Value',
        data: investedValues,
        borderColor: 'rgb(59, 130, 246)', // blue-500
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
        borderColor: 'rgb(16, 185, 129)', // green-500
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

// Chart options with dark mode support
const chartOptions = computed<ChartOptions<'line'>>(() => {
  const isDark = document.documentElement.classList.contains('dark')
  const textColor = isDark ? '#d1d5db' : '#374151' // gray-300 : gray-700
  const gridColor = isDark ? '#374151' : '#e5e7eb' // gray-700 : gray-200

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
          label: function (context) {
            let label = context.dataset.label || ''
            if (label) {
              label += ': '
            }
            if (context.parsed.y !== null) {
              label += '€' + context.parsed.y.toFixed(2)
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
          callback: function (value) {
            return '€' + Number(value).toFixed(0)
          },
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
