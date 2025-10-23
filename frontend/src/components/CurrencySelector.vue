<template>
  <div class="relative">
    <Button
      variant="ghost"
      size="sm"
      @click="showMenu = !showMenu"
      class="relative"
      aria-label="Select currency"
    >
      <span class="text-sm font-medium">{{ currencyStore.getCurrencyInfo().code }}</span>
    </Button>

    <!-- Currency selector dropdown -->
    <div
      v-if="showMenu"
      class="absolute right-0 top-full mt-2 w-48 rounded-md border bg-popover p-1 shadow-lg z-50"
      @click.stop
    >
      <button
        v-for="option in currencyOptions"
        :key="option.code"
        @click="selectCurrency(option.code)"
        class="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground transition-colors"
        :class="{ 'bg-accent text-accent-foreground': currencyStore.currency === option.code }"
      >
        <span class="font-medium">{{ option.symbol }}</span>
        <span>{{ option.code }}</span>
        <span class="text-muted-foreground">{{ option.name }}</span>
        <Check v-if="currencyStore.currency === option.code" class="ml-auto h-4 w-4" />
      </button>
    </div>

    <!-- Backdrop to close menu -->
    <div
      v-if="showMenu"
      class="fixed inset-0 z-40"
      @click="showMenu = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Check } from 'lucide-vue-next'
import { useCurrencyStore, currencyOptions, type Currency } from '../stores/currency'
import Button from './ui/Button.vue'

const currencyStore = useCurrencyStore()
const showMenu = ref(false)

function selectCurrency(currency: Currency) {
  currencyStore.setCurrency(currency)
  showMenu.value = false
}
</script>
