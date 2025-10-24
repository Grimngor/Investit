<template>
  <div
    class="rounded-xl border border-softblue-200 dark:border-gray-700 bg-white dark:bg-gray-800/60 backdrop-blur p-6 shadow-sm"
  >
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-lg font-semibold text-gray-800 dark:text-gray-200">
        {{ editingOrder ? 'Edit Order' : 'Add Manual Order' }}
      </h2>
      <button
        v-if="editingOrder"
        @click="cancelEdit"
        class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
      >
        Cancel
      </button>
    </div>

    <form @submit.prevent="submitForm" class="space-y-4">
      <!-- Date -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Date <span class="text-red-500">*</span>
        </label>
        <input
          v-model="formData.date"
          type="date"
          required
          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
          Format: YYYY-MM-DD (will be converted to DD-MM-YYYY)
        </p>
      </div>

      <!-- ISIN -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          ISIN <span class="text-red-500">*</span>
        </label>
        <input
          v-model="formData.isin"
          type="text"
          required
          placeholder="e.g., IE00BYX5NX33"
          maxlength="12"
          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <!-- Amount (EUR) -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Amount (EUR) <span class="text-red-500">*</span>
        </label>
        <input
          v-model.number="formData.amount_eur"
          type="number"
          step="0.01"
          required
          placeholder="e.g., 300.00 (negative for sell)"
          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
          Use negative value for sell orders
        </p>
      </div>

      <!-- Shares -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Shares <span class="text-red-500">*</span>
        </label>
        <input
          v-model.number="formData.shares"
          type="number"
          step="0.001"
          required
          placeholder="e.g., 24.624"
          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <!-- Status -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Status <span class="text-red-500">*</span>
        </label>
        <select
          v-model="formData.status"
          required
          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="Finalizada">Finalizada (Completed)</option>
          <option value="Pendiente">Pendiente (Pending)</option>
          <option value="Rechazada">Rechazada (Rejected)</option>
        </select>
      </div>

      <!-- Notes -->
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Notes (Optional)
        </label>
        <textarea
          v-model="formData.notes"
          rows="3"
          placeholder="Optional notes about this order"
          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
        ></textarea>
      </div>

      <!-- Actions -->
      <div class="flex gap-3 pt-4">
        <button
          type="submit"
          :disabled="submitting"
          class="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ submitting ? 'Saving...' : editingOrder ? 'Update Order' : 'Add Order' }}
        </button>
        <button
          v-if="editingOrder"
          type="button"
          @click="confirmDelete"
          :disabled="submitting"
          class="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-500 rounded-lg transition disabled:opacity-50"
        >
          Delete
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import axios from 'axios'
import { useToastStore } from '@/stores/toast'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface OrderFormData {
  date: string
  isin: string
  amount_eur: number
  shares: number
  status: string
  notes: string
}

interface Order extends OrderFormData {
  id: string
  order_type: string
}

interface Props {
  order?: Order | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'order-saved'): void
  (e: 'order-deleted'): void
}>()

const toastStore = useToastStore()
const submitting = ref(false)
const editingOrder = ref<Order | null>(null)

const formData = ref<OrderFormData>({
  date: new Date().toISOString().split('T')[0],
  isin: '',
  amount_eur: 0,
  shares: 0,
  status: 'Finalizada',
  notes: '',
})

// Watch for order prop changes (for editing)
watch(
  () => props.order,
  (newOrder) => {
    if (newOrder) {
      editingOrder.value = newOrder
      // Convert DD-MM-YYYY to YYYY-MM-DD for date input
      const dateParts = newOrder.date.split('-')
      const isoDate =
        dateParts.length === 3 ? `${dateParts[2]}-${dateParts[1]}-${dateParts[0]}` : newOrder.date

      formData.value = {
        date: isoDate,
        isin: newOrder.isin,
        amount_eur: newOrder.amount_eur,
        shares: newOrder.shares,
        status: newOrder.status,
        notes: newOrder.notes || '',
      }
    } else {
      resetForm()
    }
  },
  { immediate: true },
)

function resetForm() {
  editingOrder.value = null
  formData.value = {
    date: new Date().toISOString().split('T')[0],
    isin: '',
    amount_eur: 0,
    shares: 0,
    status: 'Finalizada',
    notes: '',
  }
}

function cancelEdit() {
  resetForm()
}

async function submitForm() {
  submitting.value = true

  try {
    const token = localStorage.getItem('token')
    // Convert YYYY-MM-DD to DD-MM-YYYY for backend
    const dateParts = formData.value.date.split('-')
    const formattedDate = `${dateParts[2]}-${dateParts[1]}-${dateParts[0]}`

    const payload = {
      ...formData.value,
      date: formattedDate,
    }

    if (editingOrder.value) {
      // Update existing order
      await axios.put(`${API_BASE_URL}/api/orders/${editingOrder.value.id}`, payload, {
        headers: { Authorization: token ? `Bearer ${token}` : '' },
      })
      toastStore.addToast('Order updated successfully', 'success')
    } else {
      // Create new order
      await axios.post(`${API_BASE_URL}/api/orders`, payload, {
        headers: { Authorization: token ? `Bearer ${token}` : '' },
      })
      toastStore.addToast('Order added successfully', 'success')
    }

    emit('order-saved')
    resetForm()
  } catch (error: any) {
    const message = error.response?.data?.detail || 'Failed to save order'
    toastStore.addToast(message, 'error')
    console.error('Order save error:', error)
  } finally {
    submitting.value = false
  }
}

async function confirmDelete() {
  if (!editingOrder.value) return

  if (!confirm('Are you sure you want to delete this order? This action cannot be undone.')) {
    return
  }

  submitting.value = true

  try {
    const token = localStorage.getItem('token')
    await axios.delete(`${API_BASE_URL}/api/orders/${editingOrder.value.id}`, {
      headers: { Authorization: token ? `Bearer ${token}` : '' },
    })

    toastStore.addToast('Order deleted successfully', 'success')
    emit('order-deleted')
    resetForm()
  } catch (error: any) {
    const message = error.response?.data?.detail || 'Failed to delete order'
    toastStore.addToast(message, 'error')
    console.error('Order delete error:', error)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped></style>
