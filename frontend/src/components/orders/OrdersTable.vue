<template>
  <div class="rounded-xl border border-softblue-200 dark:border-gray-700 bg-white dark:bg-gray-800/60 backdrop-blur shadow-sm overflow-hidden mb-6">
    <div class="px-6 py-4 border-b border-softblue-200 dark:border-gray-700 bg-softblue-50 dark:bg-gray-800/40">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">
        {{ title }}
        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-softblue-100 text-softblue-700 dark:bg-gray-700 dark:text-gray-300">
          {{ orders.length }}
        </span>
      </h2>
    </div>

    <!-- Desktop Table -->
    <div v-if="loading" class="hidden lg:block overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-softblue-100 dark:bg-gray-800/80 text-gray-700 dark:text-gray-300">
          <tr class="divide-x divide-gray-200 dark:divide-gray-700">
            <th class="px-4 py-3 text-center w-12">
              <input
                type="checkbox"
                class="rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
                :checked="allSelected"
                @change="toggleAll"
              />
            </th>
            <th class="px-4 py-3 text-left font-medium">Date</th>
            <th class="px-4 py-3 text-left font-medium">ISIN/Symbol</th>
            <th class="px-4 py-3 text-left font-medium">Ticker</th>
            <th class="px-4 py-3 text-right font-medium">Shares</th>
            <th class="px-4 py-3 text-right font-medium">Amount (EUR)</th>
            <th class="px-4 py-3 text-right font-medium">Price</th>
            <th class="px-4 py-3 text-right font-medium">Status</th>
            <th class="px-4 py-3 text-center font-medium w-24">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-softblue-200 dark:divide-gray-700">
          <tr v-for="i in 3" :key="'skel-' + i">
            <td class="px-4 py-3 text-center"><div class="h-4 w-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mx-auto"></div></td>
            <td class="px-4 py-3"><div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-full"></div></td>
            <td class="px-4 py-3"><div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-3/4"></div></td>
            <td class="px-4 py-3"><div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2"></div></td>
            <td class="px-4 py-3"><div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2 ml-auto"></div></td>
            <td class="px-4 py-3"><div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2 ml-auto"></div></td>
            <td class="px-4 py-3"><div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2 ml-auto"></div></td>
            <td class="px-4 py-3"><div class="h-6 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-16 ml-auto"></div></td>
            <td class="px-4 py-3"><div class="h-6 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-12 mx-auto"></div></td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else-if="orders.length" class="hidden lg:block overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-softblue-100 dark:bg-gray-800/80 text-gray-700 dark:text-gray-300">
          <tr class="divide-x divide-gray-200 dark:divide-gray-700">
            <th class="px-4 py-3 text-center w-12">
              <input
                type="checkbox"
                class="rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
                :checked="allSelected"
                @change="toggleAll"
              />
            </th>
            <th class="px-4 py-3 text-left font-medium">Date</th>
            <th class="px-4 py-3 text-left font-medium">ISIN/Symbol</th>
            <th class="px-4 py-3 text-left font-medium">Ticker</th>
            <th class="px-4 py-3 text-right font-medium">Shares</th>
            <th class="px-4 py-3 text-right font-medium">Amount (EUR)</th>
            <th class="px-4 py-3 text-right font-medium">Price</th>
            <th class="px-4 py-3 text-right font-medium">Status</th>
            <th class="px-4 py-3 text-center font-medium w-24">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-softblue-200 dark:divide-gray-700">
          <tr v-for="order in orders" :key="order.id" class="hover:bg-softblue-50 dark:hover:bg-gray-700/40 transition">
            <td class="px-4 py-3 text-center">
              <input
                type="checkbox"
                class="rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
                :value="order.id"
                v-model="selectedOrderIds"
              />
            </td>
            <td class="px-4 py-3">{{ formatDate(order.date) }}</td>
            <td class="px-4 py-3 font-mono text-xs" :class="order.asset_type === 'Crypto' ? 'font-bold text-purple-700 dark:text-purple-300' : ''">{{ order.isin }}</td>
            <td class="px-4 py-3 font-medium">{{ order.ticker || 'N/A' }}</td>
            <td class="px-4 py-3 text-right">{{ order.shares }}</td>
            <td class="px-4 py-3 text-right">€{{ order.amount_eur?.toFixed(2) || '0.00' }}</td>
            <td class="px-4 py-3 text-right">€{{ calculatePrice(order) }}</td>
            <td class="px-4 py-3 text-right">
              <span :class="['inline-flex px-2 py-1 rounded text-xs font-semibold', getStatusClass(order.status)]">
                {{ order.status }}
              </span>
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center justify-center gap-2">
                <button @click="$emit('edit', order)" class="p-1.5 text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/20 rounded transition" title="Edit order">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                <button @click="$emit('delete', order)" class="p-1.5 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20 rounded transition" title="Delete order">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Mobile Cards -->
    <div v-if="loading" class="lg:hidden p-4 space-y-4">
      <div v-for="i in 3" :key="'mob-skel-' + i" class="border rounded-lg p-4 space-y-3 bg-white dark:bg-gray-800">
        <div class="flex justify-between items-start">
          <div class="w-1/2">
            <div class="h-5 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-full mb-1"></div>
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-2/3"></div>
          </div>
          <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-20"></div>
        </div>
        <div class="grid grid-cols-2 gap-y-2 text-sm border-t border-gray-100 dark:border-gray-700 pt-3">
          <div class="text-gray-500 dark:text-gray-400">Date</div>
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2 ml-auto"></div>
          <div class="text-gray-500 dark:text-gray-400">Shares</div>
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2 ml-auto"></div>
          <div class="text-gray-500 dark:text-gray-400">Price</div>
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2 ml-auto"></div>
          <div class="text-gray-500 dark:text-gray-400">Total (EUR)</div>
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-1/2 ml-auto"></div>
        </div>
        <div class="pt-3 border-t border-gray-100 dark:border-gray-700 flex justify-end items-center gap-4">
          <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-16"></div>
          <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded animate-pulse w-16"></div>
        </div>
      </div>
    </div>

    <div v-if="!loading && orders.length" class="lg:hidden p-4 space-y-4">
      <div
        v-for="order in orders"
        :key="'mob-' + order.id"
        class="border rounded-lg p-4 space-y-3 bg-white dark:bg-gray-800"
      >
        <div class="flex flex-col gap-2 border-b border-gray-100 dark:border-gray-700 pb-3 mb-3">
          <div class="flex justify-between items-start">
            <div class="flex items-center gap-2">
              <input
                type="checkbox"
                class="rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
                :value="order.id"
                v-model="selectedOrderIds"
              />
              <div>
                <h3 class="font-bold text-gray-900 dark:text-white" :class="order.asset_type === 'Crypto' ? 'text-purple-700 dark:text-purple-400' : ''">
                  {{ order.isin }}
                </h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">{{ order.ticker || 'N/A' }}</p>
              </div>
            </div>
            <span :class="['inline-flex px-2 py-1 rounded text-[10px] font-semibold uppercase', getStatusClass(order.status)]">
              {{ order.status }}
            </span>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-y-2 text-sm justify-items-stretch">
          <div class="text-gray-500 dark:text-gray-400">Date</div>
          <div class="text-right font-medium">{{ formatDate(order.date) }}</div>

          <div class="text-gray-500 dark:text-gray-400">Shares</div>
          <div class="text-right font-medium">{{ order.shares }}</div>

          <div class="text-gray-500 dark:text-gray-400">Price</div>
          <div class="text-right font-medium">€{{ calculatePrice(order) }}</div>

          <div class="text-gray-500 dark:text-gray-400">Total (EUR)</div>
          <div class="text-right font-semibold">€{{ order.amount_eur?.toFixed(2) || '0.00' }}</div>
        </div>

        <div class="pt-3 border-t border-gray-100 dark:border-gray-700 flex justify-end items-center gap-4">
          <button @click="$emit('edit', order)" class="text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400 flex items-center gap-1 transition">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
            Edit
          </button>
          <button @click="$emit('delete', order)" class="text-sm font-medium text-red-600 hover:text-red-700 dark:text-red-400 flex items-center gap-1 transition">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
            Delete
          </button>
        </div>
      </div>
    </div>

    <div v-if="!loading && !orders.length" class="p-8 text-center text-gray-500 dark:text-gray-400">
      {{ emptyMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface Order {
  id?: string
  date: string
  isin: string
  ticker?: string
  shares: number
  amount_eur?: number
  status: string
  asset_type?: string
}

const props = defineProps<{
  orders: Order[]
  title: string
  emptyMessage: string
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'edit', order: Order): void
  (e: 'delete', order: Order): void
  (e: 'selection-change', selectedIds: string[]): void
}>()

const selectedOrderIds = ref<string[]>([])

// Compute if all orders are selected
const allSelected = computed(() => {
  if (props.orders.length === 0) return false
  return selectedOrderIds.value.length === props.orders.filter(o => o.id).length
})

function toggleAll(event: Event) {
  const isChecked = (event.target as HTMLInputElement).checked
  if (isChecked) {
    selectedOrderIds.value = props.orders.filter(o => o.id).map(o => o.id!)
  } else {
    selectedOrderIds.value = []
  }
}

watch(selectedOrderIds, (newVal) => {
  emit('selection-change', newVal)
}, { deep: true })

function formatDate(dateStr: string): string {
  if (!dateStr) return 'N/A'
  return dateStr
}

function calculatePrice(order: Order): string {
  if (order.amount_eur && order.shares && order.shares > 0) {
    return (order.amount_eur / order.shares).toFixed(2)
  }
  return '0.00'
}

function getStatusClass(status: string): string {
  const lowerStatus = status?.toLowerCase() || ''
  if (lowerStatus === 'finalizada') {
    return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
  } else if (lowerStatus === 'rechazada') {
    return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
  }
  return 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
}
</script>
