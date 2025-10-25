<template>
  <div class="bg-white dark:bg-gray-800/80 backdrop-blur rounded-lg border border-softblue-200 dark:border-gray-700 shadow-sm p-5 flex flex-col gap-1">
    <h3 class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">{{ label }}</h3>
    <div class="flex flex-col">
      <p :class="['text-2xl font-bold tabular-nums', valueClass || 'text-gray-800 dark:text-gray-100']">
        <span v-if="showSign">{{ value >= 0 ? '+' : '' }}</span><span v-if="prefix">{{ prefix }}</span>{{ value.toFixed(2) }}<span v-if="suffix"> {{ suffix }}</span>
      </p>
      <p v-if="percentage !== undefined" :class="['text-sm font-medium tabular-nums mt-1', valueClass || 'text-gray-600 dark:text-gray-300']">
        {{ percentage >= 0 ? '+' : '' }}{{ percentage.toFixed(2) }}%
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  label: string
  value: number
  prefix?: string
  suffix?: string
  valueClass?: string
  showSign?: boolean
  percentage?: number
}
defineProps<Props>()
</script>

<style scoped>
</style>
