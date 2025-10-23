<template>
  <div class="max-w-7xl mx-auto px-6 py-10">
    <div class="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4 mb-8">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">Orders</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">History of executed orders (coming soon)</p>
      </div>
    </div>

    <div class="rounded-xl border border-softblue-200 dark:border-gray-700 bg-softblue-50/70 dark:bg-gray-900/70 backdrop-blur shadow-sm overflow-hidden">
      <table class="w-full text-sm" v-if="orders.length">
        <thead class="bg-softblue-100/60 dark:bg-gray-800/80 text-gray-700 dark:text-gray-300">
          <tr class="divide-x divide-gray-200 dark:divide-gray-700">
            <th class="px-4 py-3 text-left font-medium">Date</th>
            <th class="px-4 py-3 text-left font-medium">Symbol</th>
            <th class="px-4 py-3 text-right font-medium">Side</th>
            <th class="px-4 py-3 text-right font-medium">Quantity</th>
            <th class="px-4 py-3 text-right font-medium">Price</th>
            <th class="px-4 py-3 text-right font-medium">Status</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-softblue-100 dark:divide-gray-800">
          <tr v-for="o in orders" :key="o.id" class="hover:bg-softblue-100/40 dark:hover:bg-gray-800/60 transition">
            <td class="px-4 py-3">{{ o.date }}</td>
            <td class="px-4 py-3 font-medium">{{ o.symbol }}</td>
            <td class="px-4 py-3 text-right">{{ o.side }}</td>
            <td class="px-4 py-3 text-right">{{ o.quantity }}</td>
            <td class="px-4 py-3 text-right">€{{ o.price.toFixed(2) }}</td>
            <td class="px-4 py-3 text-right">
              <span class="inline-flex px-2 py-1 rounded text-xs font-semibold bg-gray-100 dark:bg-gray-800">{{ o.status }}</span>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="p-12 text-center">
        <div class="text-gray-400 dark:text-gray-500 mb-2">No orders yet</div>
        <p class="text-xs text-gray-500 dark:text-gray-600">Your executed orders will appear here once available.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// Placeholder static empty list for now; will be replaced with store integration later.
interface OrderRow { id: string; date: string; symbol: string; side: 'BUY' | 'SELL'; quantity: number; price: number; status: string }
const orders = ref<OrderRow[]>([])
</script>

<style scoped></style>
