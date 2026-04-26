<template>
  <div v-if="holdings.length > 0" class="mb-4">
    <!-- Desktop Table -->
    <div v-if="loading" class="hidden lg:block overflow-x-auto">
      <table class="w-full text-sm">
        <thead :class="[tableHeadClass, 'text-gray-700 dark:text-gray-300']">
          <tr class="divide-x divide-gray-200 dark:divide-gray-700">
            <th class="px-4 py-3 text-left font-medium">Symbol</th>
            <th class="px-4 py-3 text-left font-medium">Name</th>
            <th class="px-4 py-3 text-right font-medium">Quantity</th>
            <th class="px-4 py-3 text-right font-medium">Purchase</th>
            <th class="px-4 py-3 text-right font-medium">Current</th>
            <th class="px-4 py-3 text-right font-medium">Value</th>
            <th class="px-4 py-3 text-right font-medium">Gain/Loss</th>
          </tr>
        </thead>
        <tbody :class="['divide-y', tableBodyClass]">
          <tr v-for="i in 3" :key="'skel-' + i">
            <td class="px-4 py-3"><div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-3/4"></div></td>
            <td class="px-4 py-3"><div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-full"></div></td>
            <td class="px-4 py-3"><div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2 ml-auto"></div></td>
            <td class="px-4 py-3"><div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2 ml-auto"></div></td>
            <td class="px-4 py-3"><div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2 ml-auto"></div></td>
            <td class="px-4 py-3"><div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2 ml-auto"></div></td>
            <td class="px-4 py-3"><div class="h-6 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-3/4 ml-auto"></div></td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="hidden lg:block overflow-x-auto">
      <table class="w-full text-sm">
        <thead :class="[tableHeadClass, 'text-gray-700 dark:text-gray-300']">
          <tr class="divide-x divide-gray-200 dark:divide-gray-700">
            <th class="px-4 py-3 text-left font-medium">Symbol</th>
            <th class="px-4 py-3 text-left font-medium">Name</th>
            <th class="px-4 py-3 text-right font-medium">Quantity</th>
            <th class="px-4 py-3 text-right font-medium">Purchase</th>
            <th class="px-4 py-3 text-right font-medium">Current</th>
            <th class="px-4 py-3 text-right font-medium">Value</th>
            <th class="px-4 py-3 text-right font-medium">Gain/Loss</th>
          </tr>
        </thead>
        <tbody :class="['divide-y', tableBodyClass]">
          <tr
            v-for="holding in holdings"
            :key="holding.id || holding.symbol"
            :class="[hoverRowClass, 'transition']"
          >
            <td class="px-4 py-3 font-medium">{{ holding.resolved_symbol || holding.symbol }}</td>
            <td class="px-4 py-3">{{ holding.name }}</td>
            <td class="px-4 py-3 text-right">{{ holding.quantity }}</td>
            <td class="px-4 py-3 text-right">{{ holding.purchase_price.toFixed(2) }} €</td>
            <td class="px-4 py-3 text-right">
              {{ (holding.current_price || holding.purchase_price).toFixed(2) }} €
            </td>
            <td class="px-4 py-3 text-right font-medium">
              {{ (holding.quantity * (holding.current_price || holding.purchase_price)).toFixed(2) }} €
            </td>
            <td class="px-4 py-3 text-right">
              <span
                :class="[
                  'inline-flex flex-col items-end px-2 py-1 rounded text-xs font-semibold',
                  getBadgeClass(holding),
                ]"
              >
                <span>{{ formatGainLoss(holding) }}</span>
                <span class="text-[10px] mt-0.5">{{ formatGainLossPercentage(holding) }}</span>
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mobile Cards -->
    <div v-if="loading" class="lg:hidden p-4 space-y-4">
      <div v-for="i in 3" :key="'mob-skel-' + i" class="border rounded-lg p-4 space-y-3 bg-white dark:bg-gray-800">
        <div>
          <div class="h-5 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/3 mb-1"></div>
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-2/3"></div>
        </div>
        <div class="grid grid-cols-2 gap-y-2 text-sm border-t border-gray-100 dark:border-gray-700 pt-3">
          <div class="text-gray-500 dark:text-gray-400">Quantity</div>
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2 ml-auto"></div>
          <div class="text-gray-500 dark:text-gray-400">Purchase</div>
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2 ml-auto"></div>
          <div class="text-gray-500 dark:text-gray-400">Current</div>
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2 ml-auto"></div>
          <div class="text-gray-500 dark:text-gray-400">Value</div>
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2 ml-auto"></div>
        </div>
        <div class="pt-3 border-t border-gray-100 dark:border-gray-700 flex justify-between items-center">
          <span class="text-sm text-gray-500 dark:text-gray-400">Gain/Loss</span>
          <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-16"></div>
        </div>
      </div>
    </div>

    <div v-else class="lg:hidden p-4 space-y-4">
      <div
        v-for="holding in holdings"
        :key="'mob-' + (holding.id || holding.symbol)"
        class="border rounded-lg p-4 space-y-3 bg-white dark:bg-gray-800"
      >
        <div>
          <h3 class="font-bold text-gray-900 dark:text-white">{{ holding.resolved_symbol || holding.symbol }}</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400">{{ holding.name }}</p>
        </div>

        <div class="grid grid-cols-2 gap-y-2 text-sm border-t border-gray-100 dark:border-gray-700 pt-3">
          <div class="text-gray-500 dark:text-gray-400">Quantity</div>
          <div class="text-right font-medium">{{ holding.quantity }}</div>

          <div class="text-gray-500 dark:text-gray-400">Purchase</div>
          <div class="text-right font-medium">{{ holding.purchase_price.toFixed(2) }} €</div>

          <div class="text-gray-500 dark:text-gray-400">Current</div>
          <div class="text-right font-medium">{{ (holding.current_price || holding.purchase_price).toFixed(2) }} €</div>

          <div class="text-gray-500 dark:text-gray-400">Value</div>
          <div class="text-right font-semibold">{{ (holding.quantity * (holding.current_price || holding.purchase_price)).toFixed(2) }} €</div>
        </div>

        <div class="pt-3 border-t border-gray-100 dark:border-gray-700 flex justify-between items-center">
          <span class="text-sm text-gray-500 dark:text-gray-400">Gain/Loss</span>
          <span
            :class="[
              'inline-flex flex-col items-end px-2 py-1 rounded text-xs font-semibold',
              getBadgeClass(holding),
            ]"
          >
            <span>{{ formatGainLoss(holding) }}</span>
            <span class="text-[10px] mt-0.5">{{ formatGainLossPercentage(holding) }}</span>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, computed } from 'vue'
import type { Investment } from '@/stores/portfolio'

const props = defineProps<{
  holdings: Investment[]
  theme?: 'softblue' | 'purple'
  loading?: boolean
}>()

const isPurple = computed(() => props.theme === 'purple')

const tableHeadClass = computed(() =>
  isPurple.value
    ? 'bg-purple-100 dark:bg-purple-900/30'
    : 'bg-softblue-100 dark:bg-gray-800/80'
)

const tableBodyClass = computed(() =>
  isPurple.value
    ? 'divide-purple-200 dark:divide-purple-900/40'
    : 'divide-softblue-200 dark:divide-gray-700'
)

const hoverRowClass = computed(() =>
  isPurple.value
    ? 'hover:bg-purple-50 dark:hover:bg-purple-900/20'
    : 'hover:bg-softblue-50 dark:hover:bg-gray-700/40'
)

function getGainLoss(holding: Investment): number {
  const currentPrice = holding.current_price || holding.purchase_price
  return holding.quantity * (currentPrice - holding.purchase_price)
}

function getBadgeClass(holding: Investment): string {
  return getGainLoss(holding) >= 0
    ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-300'
    : 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300'
}

function formatGainLoss(holding: Investment): string {
  const v = getGainLoss(holding)
  return `${v >= 0 ? '+' : ''}${v.toFixed(2)} €`
}

function formatGainLossPercentage(holding: Investment): string {
  const totalCost = holding.quantity * holding.purchase_price
  if (totalCost === 0) return '0.00%'
  const percentage = (getGainLoss(holding) / totalCost) * 100
  return `${percentage >= 0 ? '+' : ''}${percentage.toFixed(2)}%`
}
</script>
