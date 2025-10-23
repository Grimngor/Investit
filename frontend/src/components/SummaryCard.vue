<template>
  <div class="bg-white dark:bg-gray-800/80 backdrop-blur rounded-lg border border-softblue-200 dark:border-gray-700 shadow-sm p-5 flex flex-col gap-1">
    <h3 class="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">{{ label }}</h3>
    <p :class="['text-2xl font-bold tabular-nums text-gray-800 dark:text-gray-100', valueClass]">
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
