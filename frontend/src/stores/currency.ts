import { ref } from 'vue'
import { defineStore } from 'pinia'

export type Currency = 'EUR' | 'USD' | 'GBP'

export interface CurrencyInfo {
  code: Currency
  symbol: string
  name: string
}

export const currencyOptions: CurrencyInfo[] = [
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'GBP', symbol: '£', name: 'British Pound' }
]

export const useCurrencyStore = defineStore('currency', () => {
  const currency = ref<string>(localStorage.getItem('preferred_currency') || 'EUR')
  const rates = ref<Record<string, number>>({
    EUR: 1.0,
    USD: 1.09,
    GBP: 0.86
  })

  function setCurrency(newCurrency: string) {
    currency.value = newCurrency
    localStorage.setItem('preferred_currency', newCurrency)
  }

  function convert(amount: number, from: string, to: string): number {
    if (from === to) return amount

    // Convert to EUR first (base currency)
    const eurAmount = amount / (rates.value[from] || 1)

    // Convert from EUR to target currency
    return eurAmount * (rates.value[to] || 1)
  }

  function getCurrencyInfo(): CurrencyInfo {
    return currencyOptions.find(c => c.code === currency.value) || currencyOptions[0]
  }

  function formatCurrency(amount: number): string {
    const info = getCurrencyInfo()
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: info.code,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount)
  }

  return {
    currency,
    rates,
    setCurrency,
    convert,
    getCurrencyInfo,
    formatCurrency
  }
})
