<template>
  <div
    v-if="isVisible"
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    @click.self="$emit('close')"
  >
    <Card class="w-full max-w-2xl max-h-[90vh] overflow-y-auto m-4">
      <template #header>
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-semibold">
            {{ mode === 'edit' ? 'Edit Investment' : 'Add Investment' }}
          </h3>
          <Button variant="ghost" size="sm" @click="$emit('close')">
            <X class="h-4 w-4" />
          </Button>
        </div>
      </template>

      <form @submit.prevent="handleSubmit" class="space-y-6">
        <!-- Basic Information -->
        <div class="space-y-4">
          <h4 class="text-md font-medium">Basic Information</h4>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-2">
                Symbol / ISIN <span class="text-red-500">*</span>
              </label>
              <Input
                v-model="formData.symbol"
                placeholder="e.g., AAPL or IE0032126645"
                :class="{ 'border-red-500': errors.symbol }"
                required
              />
              <p v-if="errors.symbol" class="text-red-500 text-sm mt-1">{{ errors.symbol }}</p>
              <p class="text-muted-foreground text-xs mt-1">
                Ticker symbol or ISIN code
              </p>
            </div>

            <div>
              <label class="block text-sm font-medium mb-2">Investment Type</label>
              <select
                v-model="formData.type"
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                <option value="">Select type</option>
                <option value="ETF">ETF</option>
                <option value="Index Fund">Index Fund</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium mb-2">Name</label>
            <Input
              v-model="formData.name"
              placeholder="e.g., Apple Inc. or Vanguard S&P 500 ETF"
            />
            <p class="text-muted-foreground text-xs mt-1">
              Will be fetched automatically if available
            </p>
          </div>
        </div>

        <!-- Purchase Details -->
        <div class="space-y-4">
          <h4 class="text-md font-medium">Purchase Details</h4>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-2">
                Total Paid <span class="text-red-500">*</span>
              </label>
              <div class="relative">
                <Input
                  :value="formatDecimalInput(totalInvestmentInput)"
                  @input="handleTotalAmountInput"
                  placeholder="0.00"
                  :class="{ 'border-red-500': errors.total_amount }"
                  required
                />
                <span class="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
                  {{ currencyStore.getCurrencyInfo().code }}
                </span>
              </div>
              <p v-if="errors.total_amount" class="text-red-500 text-sm mt-1">{{ errors.total_amount }}</p>
              <p class="text-muted-foreground text-xs mt-1">
                Total amount paid for this investment
              </p>
            </div>

            <div>
              <label class="block text-sm font-medium mb-2">
                Purchase Price <span class="text-red-500">*</span>
              </label>
              <div class="relative">
                <Input
                  :value="formatDecimalInput(formData.purchase_price)"
                  @input="handlePriceInput"
                  placeholder="0.00"
                  :class="{ 'border-red-500': errors.purchase_price }"
                  required
                />
                <span class="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
                  {{ currencyStore.getCurrencyInfo().code }}
                </span>
              </div>
              <p v-if="errors.purchase_price" class="text-red-500 text-sm mt-1">{{ errors.purchase_price }}</p>
              <p class="text-muted-foreground text-xs mt-1">Price per share/unit</p>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-2">
                Quantity
              </label>
              <Input
                :value="formatDecimalInput(formData.quantity)"
                @input="handleQuantityInput"
                placeholder="0.00"
                :class="{ 'border-red-500': errors.quantity }"
              />
              <p v-if="errors.quantity" class="text-red-500 text-sm mt-1">{{ errors.quantity }}</p>
              <p class="text-muted-foreground text-xs mt-1">Number of shares/units (calculated from total paid ÷ price)</p>
            </div>

            <div>
              <label class="block text-sm font-medium mb-2">
                Purchase Date <span class="text-red-500">*</span>
              </label>
              <Input
                v-model="formData.purchase_date"
                type="date"
                :class="{ 'border-red-500': errors.purchase_date }"
                required
              />
              <p v-if="errors.purchase_date" class="text-red-500 text-sm mt-1">{{ errors.purchase_date }}</p>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium mb-2">Calculated Total</label>
            <div class="text-lg font-semibold text-primary">
              {{ currencyStore.formatCurrency(totalInvestment) }}
            </div>
            <p class="text-muted-foreground text-xs mt-1">
              Quantity × Purchase Price
            </p>
          </div>
        </div>

        <!-- Additional Information -->
        <div class="space-y-4">
          <div class="flex items-center gap-2">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              @click="showAdditionalInfo = !showAdditionalInfo"
              class="p-0 h-auto font-medium"
            >
              <ChevronDown
                class="h-4 w-4 transition-transform"
                :class="{ 'rotate-180': showAdditionalInfo }"
              />
              Additional Information (Optional)
            </Button>
          </div>
          
          <div v-if="showAdditionalInfo" class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium mb-2">Currency</label>
                <select
                  v-model="formData.currency"
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                >
                  <option value="EUR">EUR - Euro</option>
                  <option value="USD">USD - US Dollar</option>
                  <option value="GBP">GBP - British Pound</option>
                  <option value="JPY">JPY - Japanese Yen</option>
                  <option value="CAD">CAD - Canadian Dollar</option>
                </select>
              </div>

              <div>
                <label class="block text-sm font-medium mb-2">Region</label>
                <Input
                  v-model="formData.region"
                  placeholder="e.g., North America, Europe"
                />
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium mb-2">Notes</label>
              <textarea
                v-model="formData.notes"
                placeholder="Add any additional notes about this investment..."
                class="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                rows="3"
              />
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex space-x-2 pt-4 border-t">
          <Button type="submit" class="flex-1" :disabled="isLoading">
            <Loader2 v-if="isLoading" class="h-4 w-4 mr-2 animate-spin" />
            {{ mode === 'edit' ? 'Update Investment' : 'Add Investment' }}
          </Button>
          <Button type="button" variant="outline" @click="$emit('close')" :disabled="isLoading">
            Cancel
          </Button>
        </div>
      </form>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { X, Loader2, ChevronDown } from 'lucide-vue-next'
import Card from './ui/Card.vue'
import Button from './ui/Button.vue'
import Input from './ui/Input.vue'
import { useCurrencyStore } from '../stores/currency'

const currencyStore = useCurrencyStore()

export interface InvestmentFormData {
  id?: string
  symbol: string
  name: string
  type: string
  quantity: number
  purchase_price: number
  purchase_date: string
  currency: string
  sector: string
  region: string
  risk_rating: string
  notes: string
}

interface Props {
  isVisible: boolean
  mode: 'add' | 'edit'
  initialData?: Partial<InvestmentFormData>
  isLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  initialData: () => ({}),
})

const emit = defineEmits<{
  'close': []
  'submit': [data: InvestmentFormData]
}>()

// Form data
const formData = ref<InvestmentFormData>({
  symbol: '',
  name: '',
  type: 'Index Fund', // Default to Index Fund
  quantity: 0,
  purchase_price: 0,
  purchase_date: new Date().toISOString().split('T')[0],
  currency: 'EUR', // Default to EUR
  sector: '',
  region: '',
  risk_rating: '',
  notes: '',
})

// Form validation
const errors = ref<Record<string, string>>({})

// UI state
const showAdditionalInfo = ref(false) // Collapsed by default
const totalInvestmentInput = ref(0)
const isEditingTotal = ref(false) // Track when user is editing total field

// Computed values
const totalInvestment = computed(() => {
  return (formData.value.quantity || 0) * (formData.value.purchase_price || 0)
})

// Decimal input formatting and parsing functions
function formatDecimalInput(value: number): string {
  if (value === 0) return ''
  return value.toString()
}

function parseDecimalInput(value: string): number {
  if (!value) return 0
  // Replace commas with dots for consistent decimal parsing
  const normalizedValue = value.replace(',', '.')
  const parsed = parseFloat(normalizedValue)
  return isNaN(parsed) ? 0 : parsed
}

function handleQuantityInput(event: Event) {
  const target = event.target as HTMLInputElement
  const value = parseDecimalInput(target.value)
  formData.value.quantity = value
  
  // Update total when both quantity and price are available
  if (value > 0 && formData.value.purchase_price > 0) {
    totalInvestmentInput.value = totalInvestment.value
  }
}

function handlePriceInput(event: Event) {
  const target = event.target as HTMLInputElement
  const value = parseDecimalInput(target.value)
  formData.value.purchase_price = value
  
  // Update total when both quantity and price are available
  if (value > 0 && formData.value.quantity > 0) {
    totalInvestmentInput.value = totalInvestment.value
  } else if (totalInvestmentInput.value > 0 && value > 0) {
    // Recalculate quantity from total amount if we have total and price
    formData.value.quantity = totalInvestmentInput.value / value
  }
}

function handleTotalAmountInput(event: Event) {
  const target = event.target as HTMLInputElement
  const value = parseDecimalInput(target.value)
  totalInvestmentInput.value = value
  isEditingTotal.value = true
  
  // Calculate quantity from total amount if price is set
  if (formData.value.purchase_price > 0) {
    formData.value.quantity = value / formData.value.purchase_price
  }
  
  // Reset the editing flag after a short delay
  setTimeout(() => {
    isEditingTotal.value = false
  }, 1000)
}

// Watchers
watch(() => props.initialData, (newData) => {
  if (newData && Object.keys(newData).length > 0) {
    formData.value = {
      ...formData.value,
      ...newData,
    }
    totalInvestmentInput.value = totalInvestment.value
  }
}, { immediate: true, deep: true })

// Watch for changes in quantity and purchase_price to keep total in sync
watch([() => formData.value.quantity, () => formData.value.purchase_price], ([newQuantity, newPrice]) => {
  // Only auto-update total if both values are greater than 0 and the user isn't currently editing the total
  if (newQuantity > 0 && newPrice > 0 && !isEditingTotal.value) {
    const calculatedTotal = newQuantity * newPrice
    // Only update if the calculated total is significantly different from current input
    if (Math.abs(totalInvestmentInput.value - calculatedTotal) > 0.01) {
      totalInvestmentInput.value = calculatedTotal
    }
  }
})

watch(() => props.isVisible, (visible) => {
  if (!visible) {
    // Reset form when modal closes
    setTimeout(() => {
      if (props.mode === 'add') {
        formData.value = {
          symbol: '',
          name: '',
          type: 'Index Fund', // Default to Index Fund
          quantity: 0,
          purchase_price: 0,
          purchase_date: new Date().toISOString().split('T')[0],
          currency: 'EUR', // Default to EUR
          sector: '',
          region: '',
          risk_rating: '',
          notes: '',
        }
        totalInvestmentInput.value = 0
      }
      errors.value = {}
      showAdditionalInfo.value = false // Reset to collapsed
    }, 300)
  }
})

// Methods
function validateForm(): boolean {
  errors.value = {}

  if (!formData.value.symbol.trim()) {
    errors.value.symbol = 'Symbol or ISIN is required'
  }

  if (!formData.value.purchase_price || formData.value.purchase_price <= 0) {
    errors.value.purchase_price = 'Purchase price must be greater than 0'
  }

  // Either total amount OR quantity must be provided
  const hasTotalAmount = totalInvestmentInput.value > 0
  const hasQuantity = formData.value.quantity > 0

  if (!hasTotalAmount && !hasQuantity) {
    errors.value.total_amount = 'Either total paid or quantity must be provided'
    errors.value.quantity = 'Either total paid or quantity must be provided'
  }

  if (!formData.value.purchase_date) {
    errors.value.purchase_date = 'Purchase date is required'
  }

  const purchaseDate = new Date(formData.value.purchase_date)
  const today = new Date()
  if (purchaseDate > today) {
    errors.value.purchase_date = 'Purchase date cannot be in the future'
  }

  return Object.keys(errors.value).length === 0
}

function handleSubmit() {
  if (validateForm()) {
    // Ensure we have both quantity and total amount calculated
    if (totalInvestmentInput.value > 0 && formData.value.quantity === 0) {
      formData.value.quantity = totalInvestmentInput.value / formData.value.purchase_price
    }
    if (formData.value.quantity > 0 && totalInvestmentInput.value === 0) {
      totalInvestmentInput.value = formData.value.quantity * formData.value.purchase_price
    }

    // Send simplified data that matches the backend Investment model
    const investmentData = {
      symbol: formData.value.symbol.toUpperCase().trim(),
      name: formData.value.name || formData.value.symbol.toUpperCase().trim(),
      type: formData.value.type,
      quantity: formData.value.quantity,
      purchase_price: formData.value.purchase_price,
      purchase_date: formData.value.purchase_date,
      currency: formData.value.currency,
      sector: formData.value.sector,
      region: formData.value.region,
      risk_rating: formData.value.risk_rating,
      notes: formData.value.notes,
    }

    emit('submit', investmentData)
  }
}
</script>
