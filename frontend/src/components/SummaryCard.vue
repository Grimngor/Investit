<template>
  <div class="bg-white dark:bg-gray-900/70 backdrop-blur rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-5 flex flex-col gap-1">
    <h3 class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">{{ label }}</h3>
    <p :class="['text-2xl font-bold tabular-nums', valueClass]">
      <span v-if="prefix">{{ prefix }}</span>{{ value.toFixed(2) }}
    </p>
  </div>
</template>

<script setup lang="ts">
interface Props {
  label: string
  value: number
  prefix?: string
  valueClass?: string
}
defineProps<Props>()
</script>

<style scoped>
</style>
