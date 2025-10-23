<template>
  <div class="space-y-4">
    <!-- Table Controls -->
    <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
      <!-- Search and Filters -->
      <div class="flex flex-col sm:flex-row gap-4 flex-1">
        <div class="relative">
          <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            v-model="searchQuery"
            placeholder="Search investments..."
            class="pl-10 w-full sm:w-64"
          />
        </div>
        
        <div class="relative">
          <select
            v-model="typeFilter"
            class="flex h-10 w-full sm:w-48 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 appearance-none pr-8"
          >
            <option value="">All Types</option>
            <option value="ETF">ETF</option>
            <option value="Index Fund">Index Fund</option>
            <option value="Stock">Stock</option>
          </select>
          <div class="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
            <ChevronDown class="h-4 w-4 text-muted-foreground" />
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-2">
        <Button variant="outline" @click="exportData">
          <Download class="h-4 w-4 mr-2" />
          Export
        </Button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex justify-center py-8">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-8 text-red-600">
      {{ error }}
      <Button variant="outline" class="mt-4" @click="$emit('retry')">
        Retry
      </Button>
    </div>

    <!-- Empty State -->
    <div v-else-if="filteredAndSortedData.length === 0 && !searchQuery && !typeFilter" class="text-center py-8">
      <div class="text-muted-foreground mb-4">
        No investments yet. Add your first investment to get started.
      </div>
      <Button @click="$emit('add-investment')">
        <Plus class="h-4 w-4 mr-2" />
        Add Investment
      </Button>
    </div>

    <!-- No Results State -->
    <div v-else-if="filteredAndSortedData.length === 0" class="text-center py-8">
      <div class="text-muted-foreground mb-4">
        No investments match your current filters.
      </div>
      <Button variant="outline" @click="clearFilters">
        Clear Filters
      </Button>
    </div>

    <!-- Data Table -->
    <Card v-else>
      <!-- Desktop Table -->
      <div class="hidden lg:block overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b text-left">
              <th
                v-for="column in columns"
                :key="column.key"
                class="pb-3 font-medium cursor-pointer hover:text-primary transition-colors"
                @click="handleSort(column.key)"
                :tabindex="0"
                @keydown.enter="handleSort(column.key)"
                @keydown.space.prevent="handleSort(column.key)"
                role="button"
                :aria-label="`Sort by ${column.label}`"
              >
                <div class="flex items-center gap-2">
                  {{ column.label }}
                  <div class="flex flex-col">
                    <ChevronUp
                      class="h-3 w-3"
                      :class="[
                        sortKey === column.key && sortOrder === 'asc'
                          ? 'text-primary'
                          : 'text-muted-foreground'
                      ]"
                    />
                    <ChevronDown
                      class="h-3 w-3"
                      :class="[
                        sortKey === column.key && sortOrder === 'desc'
                          ? 'text-primary'
                          : 'text-muted-foreground'
                      ]"
                    />
                  </div>
                </div>
              </th>
              <th class="pb-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(item, index) in paginatedData"
              :key="item.id"
              class="border-b hover:bg-muted/50 transition-colors"
            >
              <td
                v-for="column in columns"
                :key="column.key"
                class="py-3"
                :class="column.class"
              >
                <component
                  :is="column.component || 'span'"
                  v-bind="column.props ? column.props(item) : {}"
                >
                  {{ column.format ? column.format(item[column.key], item) : item[column.key] }}
                </component>
              </td>
              <td class="py-3">
                <div class="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    @click="$emit('edit-investment', item)"
                    :disabled="item.loading"
                    :aria-label="`Edit ${item.symbol || item.name}`"
                  >
                    <Edit2 class="h-4 w-4" />
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    @click="$emit('delete-investment', item.id)"
                    :disabled="item.loading"
                    :aria-label="`Delete ${item.symbol || item.name}`"
                  >
                    <Trash2 class="h-4 w-4" />
                  </Button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Mobile Cards -->
      <div class="lg:hidden space-y-4">
        <div
          v-for="item in paginatedData"
          :key="item.id"
          class="border rounded-lg p-4 space-y-2"
        >
          <div class="flex justify-between items-start">
            <div>
              <h3 class="font-medium">{{ item.symbol || item.name }}</h3>
              <p class="text-sm text-muted-foreground">{{ item.name || item.symbol }}</p>
            </div>
            <div class="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                @click="$emit('edit-investment', item)"
                :disabled="item.loading"
                :aria-label="`Edit ${item.symbol || item.name}`"
              >
                <Edit2 class="h-4 w-4" />
              </Button>
              <Button
                variant="destructive"
                size="sm"
                @click="$emit('delete-investment', item.id)"
                :disabled="item.loading"
                :aria-label="`Delete ${item.symbol || item.name}`"
              >
                <Trash2 class="h-4 w-4" />
              </Button>
            </div>
          </div>
          
          <div class="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span class="text-muted-foreground">Quantity:</span>
              <span class="ml-2">{{ formatNumber(item.quantity, 3) }}</span>
            </div>
            <div>
              <span class="text-muted-foreground">Price:</span>
              <span class="ml-2">{{ currencyStore.formatCurrency(item.purchase_price) }}</span>
            </div>
            <div>
              <span class="text-muted-foreground">Current:</span>
              <span class="ml-2">
                {{ item.current_price ? currencyStore.formatCurrency(item.current_price) : '-' }}
              </span>
            </div>
            <div>
              <span class="text-muted-foreground">Value:</span>
              <span class="ml-2">
                {{ currencyStore.formatCurrency(item.market_value || (item.quantity * item.purchase_price)) }}
              </span>
            </div>
          </div>
          
          <div
            class="text-sm"
            :class="(item.gain_loss || 0) >= 0 ? 'text-green-600' : 'text-red-600'"
          >
            <span class="text-muted-foreground">Gain/Loss:</span>
            <span class="ml-2">
              {{ (item.gain_loss || 0) >= 0 ? '+' : '' }}{{ currencyStore.formatCurrency(Math.abs(item.gain_loss || 0)) }}
              ({{ (item.gain_loss_percent || 0) >= 0 ? '+' : '' }}{{ (item.gain_loss_percent || 0).toFixed(2) }}%)
            </span>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="px-6 py-4 border-t">
        <div class="flex items-center justify-between">
          <div class="text-sm text-muted-foreground">
            Showing {{ startItem }} to {{ endItem }} of {{ filteredAndSortedData.length }} results
          </div>
          
          <div class="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              :disabled="currentPage === 1"
              @click="currentPage = 1"
            >
              <ChevronsLeft class="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              :disabled="currentPage === 1"
              @click="currentPage--"
            >
              <ChevronLeft class="h-4 w-4" />
            </Button>
            
            <div class="flex gap-1">
              <Button
                v-for="page in visiblePages"
                :key="page"
                :variant="page === currentPage ? 'default' : 'outline'"
                size="sm"
                @click="typeof page === 'number' ? currentPage = page : null"
                :disabled="typeof page === 'string'"
              >
                {{ page }}
              </Button>
            </div>
            
            <Button
              variant="outline"
              size="sm"
              :disabled="currentPage === totalPages"
              @click="currentPage++"
            >
              <ChevronRight class="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              :disabled="currentPage === totalPages"
              @click="currentPage = totalPages"
            >
              <ChevronsRight class="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  Search,
  Download,
  Plus,
  Edit2,
  Trash2,
  ChevronUp,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from 'lucide-vue-next'
import Card from './ui/Card.vue'
import Button from './ui/Button.vue'
import Input from './ui/Input.vue'
import { useCurrencyStore } from '../stores/currency'

const currencyStore = useCurrencyStore()

export interface TableColumn {
  key: string
  label: string
  sortable?: boolean
  format?: (value: any, item: any) => string
  class?: string
  component?: string
  props?: (item: any) => Record<string, any>
}

interface Props {
  data: any[]
  columns: TableColumn[]
  isLoading?: boolean
  error?: string
  pageSize?: number
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  error: '',
  pageSize: 10,
})

const emit = defineEmits<{
  'add-investment': []
  'edit-investment': [item: any]
  'delete-investment': [id: string]
  'retry': []
}>()

// Search and filtering
const searchQuery = ref('')
const typeFilter = ref('')

// Sorting
const sortKey = ref('')
const sortOrder = ref<'asc' | 'desc'>('asc')

// Pagination
const currentPage = ref(1)

// Computed values
const filteredAndSortedData = computed(() => {
  let filtered = props.data

  // Apply search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(item =>
      Object.values(item).some(value =>
        String(value).toLowerCase().includes(query)
      )
    )
  }

  // Apply type filter
  if (typeFilter.value) {
    filtered = filtered.filter(item => item.type === typeFilter.value)
  }

  // Apply sorting
  if (sortKey.value) {
    filtered = [...filtered].sort((a, b) => {
      const aVal = a[sortKey.value]
      const bVal = b[sortKey.value]
      
      let comparison = 0
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        comparison = aVal - bVal
      } else {
        comparison = String(aVal).localeCompare(String(bVal))
      }
      
      return sortOrder.value === 'asc' ? comparison : -comparison
    })
  }

  return filtered
})

const totalPages = computed(() => 
  Math.ceil(filteredAndSortedData.value.length / props.pageSize)
)

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * props.pageSize
  const end = start + props.pageSize
  return filteredAndSortedData.value.slice(start, end)
})

const startItem = computed(() => 
  filteredAndSortedData.value.length === 0 ? 0 : (currentPage.value - 1) * props.pageSize + 1
)

const endItem = computed(() => 
  Math.min(currentPage.value * props.pageSize, filteredAndSortedData.value.length)
)

const visiblePages = computed(() => {
  const pages: (number | string)[] = []
  const total = totalPages.value
  const current = currentPage.value
  
  if (total <= 7) {
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    if (current <= 4) {
      for (let i = 1; i <= 5; i++) {
        pages.push(i)
      }
      pages.push('...', total)
    } else if (current >= total - 3) {
      pages.push(1, '...')
      for (let i = total - 4; i <= total; i++) {
        pages.push(i)
      }
    } else {
      pages.push(1, '...')
      for (let i = current - 1; i <= current + 1; i++) {
        pages.push(i)
      }
      pages.push('...', total)
    }
  }
  
  return pages.filter((p, index) => p !== '...' || pages.indexOf(p) === index) as (number | string)[]
})

// Methods
function handleSort(key: string) {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'asc'
  }
}

function clearFilters() {
  searchQuery.value = ''
  typeFilter.value = ''
  currentPage.value = 1
}

function exportData() {
  // Simple CSV export
  const csvContent = [
    props.columns.map(col => col.label).join(','),
    ...filteredAndSortedData.value.map(item =>
      props.columns.map(col => {
        const value = col.format ? col.format(item[col.key], item) : item[col.key]
        return `"${String(value).replace(/"/g, '""')}"`
      }).join(',')
    )
  ].join('\n')
  
  const blob = new Blob([csvContent], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'investments.csv'
  a.click()
  URL.revokeObjectURL(url)
}

// Reset pagination when filters change
watch([searchQuery, typeFilter], () => {
  currentPage.value = 1
})

// Utility functions for mobile view
const formatNumber = (value: number, decimals: number = 2) => {
  return value.toFixed(decimals)
}
</script>
