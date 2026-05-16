<template>
	<div
		v-if="isOpen"
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
		@click.self="close"
	>
		<div
			class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto m-4"
		>
			<!-- Header -->
			<div
				class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700"
			>
				<h2 class="text-xl font-semibold text-gray-800 dark:text-gray-200">Edit Order</h2>
				<button
					@click="close"
					class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
				>
					<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M6 18L18 6M6 6l12 12"
						/>
					</svg>
				</button>
			</div>

			<!-- Form -->
			<form @submit.prevent="handleSubmit" class="p-6 space-y-6">
				<!-- Date -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						Order Date
					</label>
					<input
						v-model="formData.date"
						type="date"
						required
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
					/>
				</div>

				<!-- ISIN -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						ISIN
					</label>
					<input
						v-model="formData.isin"
						type="text"
						required
						maxlength="12"
						minlength="12"
						placeholder="e.g., IE00B4L5Y983"
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono"
					/>
					<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">12 characters exactly</p>
				</div>

				<!-- Ticker (Optional) -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						Ticker (Optional)
					</label>
					<input
						v-model="formData.ticker"
						type="text"
						placeholder="e.g., IWDA"
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
					/>
				</div>

				<!-- Amount & Shares (Grid) -->
				<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Amount (EUR)
						</label>
						<input
							v-model.number="formData.amount_eur"
							type="number"
							step="0.01"
							min="0.01"
							required
							placeholder="0.00"
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						/>
					</div>
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Shares
						</label>
						<input
							v-model.number="formData.shares"
							type="number"
							step="0.0001"
							min="0.0001"
							required
							placeholder="0.0000"
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						/>
					</div>
				</div>

				<!-- Computed Price (Read-only) -->
				<div class="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
					<div class="text-sm text-gray-600 dark:text-gray-400">Price per Share (Calculated)</div>
					<div class="text-lg font-semibold text-gray-800 dark:text-gray-200 mt-1">
						€{{ calculatePricePerShare() }}
					</div>
				</div>

				<!-- Order Type & Status (Grid) -->
				<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Order Type
						</label>
						<select
							v-model="formData.order_type"
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						>
							<option value="buy">Buy</option>
							<option value="sell">Sell</option>
						</select>
					</div>
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Status
						</label>
						<select
							v-model="formData.status"
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						>
							<option value="Finalizada">Finalizada</option>
							<option value="Rechazada">Rechazada</option>
						</select>
					</div>
				</div>

				<!-- Notes (Optional) -->
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
						Notes (Optional)
					</label>
					<textarea
						v-model="formData.notes"
						rows="3"
						placeholder="Any additional notes about this order..."
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
					></textarea>
				</div>

				<!-- Actions -->
				<div class="flex flex-col-reverse sm:flex-row sm:justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
					<button
						type="button"
						@click="close"
						:disabled="saving"
						class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition disabled:opacity-50"
					>
						Cancel
					</button>
					<button
						type="submit"
						:disabled="saving || !isValid"
						class="px-6 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
					>
						<svg
							v-if="saving"
							class="animate-spin h-4 w-4"
							fill="none"
							viewBox="0 0 24 24"
						>
							<circle
								class="opacity-25"
								cx="12"
								cy="12"
								r="10"
								stroke="currentColor"
								stroke-width="4"
							></circle>
							<path
								class="opacity-75"
								fill="currentColor"
								d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
							></path>
						</svg>
						<span>{{ saving ? 'Saving...' : 'Save Changes' }}</span>
					</button>
				</div>
			</form>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { apiClient } from '@/services/api'
import { useToastStore } from '@/stores/toast'

interface Order {
	id?: string
	date: string
	isin: string
	ticker?: string
	shares: number
	amount_eur?: number
	order_type?: string
	status: string
	notes?: string
}

interface Props {
	order: Order | null
	isOpen: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
	(e: 'close'): void
	(e: 'saved'): void
}>()

const toastStore = useToastStore()
const saving = ref(false)

const formData = ref<Order>({
	date: '',
	isin: '',
	ticker: '',
	shares: 0,
	amount_eur: 0,
	order_type: 'buy',
	status: 'Finalizada',
	notes: ''
})

// Watch for order changes and populate form
watch(
	() => props.order,
	(newOrder) => {
		if (newOrder) {
			// Convert DD/MM/YYYY to YYYY-MM-DD for date input
			let isoDate = newOrder.date
			if (newOrder.date && newOrder.date.includes('/')) {
				const [day, month, year] = newOrder.date.split('/')
				isoDate = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`
			}

			formData.value = {
				date: isoDate,
				isin: newOrder.isin || '',
				ticker: newOrder.ticker || '',
				shares: newOrder.shares || 0,
				amount_eur: newOrder.amount_eur || 0,
				order_type: newOrder.order_type || 'buy',
				status: newOrder.status || 'Finalizada',
				notes: newOrder.notes || ''
			}
		}
	},
	{ immediate: true }
)

const isValid = computed(() => {
	return (
		formData.value.date &&
		formData.value.isin?.length === 12 &&
		formData.value.shares > 0 &&
		formData.value.amount_eur &&
		formData.value.amount_eur > 0
	)
})

function calculatePricePerShare(): string {
	if (formData.value.amount_eur && formData.value.shares && formData.value.shares > 0) {
		return (formData.value.amount_eur / formData.value.shares).toFixed(4)
	}
	return '0.0000'
}

async function handleSubmit() {
	if (!isValid.value || !props.order?.id) return

	saving.value = true
	try {
		// Convert YYYY-MM-DD back to DD/MM/YYYY for backend
		const [year, month, day] = formData.value.date.split('-')
		const ddmmyyyy = `${day}/${month}/${year}`

		const updateData: Record<string, any> = {
			date: ddmmyyyy,
			isin: formData.value.isin,
			amount_eur: formData.value.amount_eur,
			shares: formData.value.shares,
			order_type: formData.value.order_type,
			status: formData.value.status
		}

		// Only include optional fields if they have values
		if (formData.value.ticker) {
			updateData.ticker = formData.value.ticker
		}
		if (formData.value.notes) {
			updateData.notes = formData.value.notes
		}

		await apiClient.updateOrder(props.order.id, updateData)
		toastStore.addToast('Order updated successfully', 'success')
		emit('saved')
		close()
	} catch (error: any) {
		const errorMsg = error.response?.data?.detail || 'Failed to update order'
		console.error('Order update error:', error)
		toastStore.addToast(errorMsg, 'error')
	} finally {
		saving.value = false
	}
}

function close() {
	emit('close')
}
</script>

<style scoped>
.animate-spin {
	animation: spin 1s linear infinite;
}

@keyframes spin {
	from {
		transform: rotate(0deg);
	}
	to {
		transform: rotate(360deg);
	}
}
</style>
