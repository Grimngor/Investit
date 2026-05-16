<template>
	<Teleport to="body">
		<div
			v-if="isOpen"
			class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm"
			@click.self="close"
		>
			<div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-6xl max-h-[90vh] overflow-hidden m-4 flex flex-col">
				<div class="flex items-start justify-between gap-4 p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700">
					<div class="min-w-0">
						<h2 class="text-xl font-semibold text-gray-800 dark:text-gray-200">Preview & Edit CSV Import</h2>
						<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
							Review {{ parsedOrders.length }} orders: {{ importableOrders.length }} new, {{ skippedOrders.length }} already present
						</p>
					</div>
					<button @click="close" class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition">
						<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>

				<div class="flex-1 overflow-auto p-4 sm:p-6">
					<table class="w-full text-sm border border-gray-200 dark:border-gray-700 rounded-lg">
						<thead class="bg-gray-100 dark:bg-gray-800 sticky top-0">
							<tr>
								<th class="px-3 py-2 text-left text-xs font-medium">#</th>
								<th class="px-3 py-2 text-left text-xs font-medium">Date</th>
								<th class="px-3 py-2 text-left text-xs font-medium">ISIN</th>
								<th class="px-3 py-2 text-left text-xs font-medium">Amount (EUR)</th>
								<th class="px-3 py-2 text-left text-xs font-medium">Shares</th>
								<th class="px-3 py-2 text-left text-xs font-medium">Status</th>
								<th class="px-3 py-2 text-left text-xs font-medium">Import</th>
								<th class="px-3 py-2 text-center text-xs font-medium w-16">Action</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
							<tr
								v-for="(order, idx) in parsedOrders"
								:key="idx"
								:class="[
									editingIndex === idx
										? 'bg-blue-50 dark:bg-blue-900/20'
										: order.import_status === 'already_present'
											? 'bg-gray-50 dark:bg-gray-900/30 opacity-75'
											: 'hover:bg-gray-50 dark:hover:bg-gray-700/40',
								]"
							>
								<td class="px-3 py-2 text-gray-500 dark:text-gray-400 text-xs">{{ idx + 1 }}</td>
								<td class="px-3 py-2">
									<input
										v-if="editingIndex === idx"
										v-model="editForm.date"
										type="date"
										class="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200"
									/>
									<span v-else class="text-xs">{{ order.date }}</span>
								</td>
								<td class="px-3 py-2">
									<input
										v-if="editingIndex === idx"
										v-model="editForm.isin"
										type="text"
										maxlength="12"
										class="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200 font-mono"
									/>
									<span v-else class="text-xs font-mono">{{ order.isin }}</span>
								</td>
								<td class="px-3 py-2">
									<input
										v-if="editingIndex === idx"
										v-model.number="editForm.amount_eur"
										type="number"
										step="0.01"
										class="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200"
									/>
									<span v-else class="text-xs">EUR {{ order.amount_eur?.toFixed(2) }}</span>
								</td>
								<td class="px-3 py-2">
									<input
										v-if="editingIndex === idx"
										v-model.number="editForm.shares"
										type="number"
										step="0.0001"
										class="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200"
									/>
									<span v-else class="text-xs">{{ order.shares }}</span>
								</td>
								<td class="px-3 py-2">
									<select
										v-if="editingIndex === idx"
										v-model="editForm.status"
										class="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200"
									>
										<option value="Finalizada">Finalizada</option>
										<option value="Rechazada">Rechazada</option>
									</select>
									<span
										v-else
										:class="[
											'inline-flex px-2 py-0.5 rounded text-xs font-semibold',
											order.status === 'Finalizada'
												? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
												: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300',
										]"
									>
										{{ order.status }}
									</span>
								</td>
								<td class="px-3 py-2">
									<span
										:class="[
											'inline-flex px-2 py-0.5 rounded text-xs font-semibold',
											order.import_status === 'already_present'
												? 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
												: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
										]"
									>
										{{ order.import_status === 'already_present' ? 'Already present' : 'New' }}
									</span>
								</td>
								<td class="px-3 py-2">
									<div v-if="editingIndex === idx" class="flex gap-1 justify-center">
										<button
											@click="saveEdit(idx)"
											class="p-1 text-green-600 hover:bg-green-50 dark:text-green-400 dark:hover:bg-green-900/20 rounded"
											title="Save"
										>
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
											</svg>
										</button>
										<button
											@click="cancelEdit"
											class="p-1 text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-gray-700 rounded"
											title="Cancel"
										>
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
											</svg>
										</button>
									</div>
									<div v-else-if="order.import_status === 'already_present'" class="text-center text-xs text-gray-400">-</div>
									<div v-else class="flex gap-1 justify-center">
										<button
											@click="startEdit(idx, order)"
											class="p-1 text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/20 rounded"
											title="Edit"
										>
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
												/>
											</svg>
										</button>
										<button
											@click="removeOrder(idx)"
											class="p-1 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20 rounded"
											title="Remove"
										>
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
												/>
											</svg>
										</button>
									</div>
								</td>
							</tr>
						</tbody>
					</table>

					<div v-if="parsedOrders.length === 0" class="text-center py-12 text-gray-400">No valid orders found in CSV</div>
				</div>

				<div class="flex flex-col gap-4 p-4 sm:p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/30 sm:flex-row sm:items-center sm:justify-between">
					<div class="text-sm text-gray-600 dark:text-gray-400">
						<span class="font-medium text-gray-800 dark:text-gray-200">{{ importableOrders.length }}</span>
						new orders ready to import
					</div>
					<div class="flex flex-col-reverse gap-3 sm:flex-row">
						<button
							@click="close"
							:disabled="importing"
							class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 border border-gray-300 dark:border-gray-600 rounded-lg transition disabled:opacity-50"
						>
							Cancel
						</button>
						<button
							@click="handleImport"
							:disabled="importing || importableOrders.length === 0"
							class="px-6 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
						>
							<svg v-if="importing" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path
									class="opacity-75"
									fill="currentColor"
									d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
								></path>
							</svg>
							<span>{{ importing ? 'Importing...' : importableOrders.length === 0 ? 'Nothing New' : 'Import Orders' }}</span>
						</button>
					</div>
				</div>
			</div>
		</div>
	</Teleport>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import axios from 'axios'
import { useToastStore } from '@/stores/toast'
import { API_BASE_URL } from '@/services/config'

interface CSVOrder {
	date: string
	isin: string
	amount_eur: number
	shares: number
	status: string
	order_type?: 'buy' | 'sell'
	import_status?: 'new' | 'already_present'
	existing_order_id?: string | null
	asset_type?: string
}

interface Props {
	file: File | null
	isOpen: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
	(e: 'close'): void
	(e: 'imported', result: { imported_count: number; rejected_count?: number; skipped_count?: number }): void
}>()

const toastStore = useToastStore()
const parsedOrders = ref<CSVOrder[]>([])
const importing = ref(false)
const editingIndex = ref<number | null>(null)
const importableOrders = computed(() => parsedOrders.value.filter((order) => order.import_status !== 'already_present'))
const skippedOrders = computed(() => parsedOrders.value.filter((order) => order.import_status === 'already_present'))
const editForm = ref<CSVOrder>({
	date: '',
	isin: '',
	amount_eur: 0,
	shares: 0,
	status: 'Finalizada',
	import_status: 'new',
})

watch(
	() => [props.file, props.isOpen] as const,
	async ([newFile, isOpen]) => {
		if (newFile && isOpen) {
			await previewCSV(newFile)
		}
	},
	{ immediate: true },
)

async function previewCSV(file: File) {
	importing.value = true
	try {
		const formData = new FormData()
		formData.append('file', file)
		const token = localStorage.getItem('token')
		const response = await axios.post(`${API_BASE_URL}/api/orders/import-csv/preview`, formData, {
			headers: {
				'Content-Type': 'multipart/form-data',
				Authorization: token ? `Bearer ${token}` : '',
			},
		})
		parsedOrders.value = response.data.orders || []
		if (parsedOrders.value.length === 0) {
			toastStore.addToast('No valid orders found in CSV', 'warning')
		}
		if (response.data.errors?.length) {
			toastStore.addToast(`CSV parsed with ${response.data.errors.length} warnings`, 'warning')
		}
	} catch (error) {
		console.error('CSV preview error:', error)
		toastStore.addToast('Failed to parse CSV file', 'error')
	} finally {
		importing.value = false
	}
}

function startEdit(idx: number, order: CSVOrder) {
	if (order.import_status === 'already_present') return
	editingIndex.value = idx
	editForm.value = { ...order }
}

function saveEdit(idx: number) {
	parsedOrders.value[idx] = { ...editForm.value, import_status: 'new' }
	editingIndex.value = null
}

function cancelEdit() {
	editingIndex.value = null
}

function removeOrder(idx: number) {
	if (parsedOrders.value[idx]?.import_status === 'already_present') return
	parsedOrders.value.splice(idx, 1)
}

async function handleCryptoImport(file: File) {
	importing.value = true
	try {
		const formData = new FormData()
		formData.append('file', file)

		const token = localStorage.getItem('token')
		const response = await axios.post(`${API_BASE_URL}/api/orders/import-csv`, formData, {
			headers: {
				'Content-Type': 'multipart/form-data',
				Authorization: token ? `Bearer ${token}` : '',
			},
		})

		toastStore.addToast(
			`Successfully imported ${response.data.imported_count} crypto orders and skipped ${response.data.skipped_count || 0}`,
			'success',
		)
		emit('imported', {
			imported_count: response.data.imported_count,
			rejected_count: response.data.rejected_count,
			skipped_count: response.data.skipped_count || 0,
		})
		close()
	} catch (error: any) {
		const message = error.response?.data?.detail || 'Failed to import crypto orders'
		toastStore.addToast(message, 'error')
	} finally {
		importing.value = false
	}
}

async function handleImport() {
	if (importableOrders.value.length === 0) return

	const isCryptoOrders = importableOrders.value.every((order) => order.isin && order.isin.length >= 3 && order.isin.length <= 5)
	if (isCryptoOrders && props.file) {
		await handleCryptoImport(props.file)
		return
	}

	importing.value = true
	try {
		const csvHeader = 'Fecha de la orden;ISIN;Importe estimado;Numero de participaciones;Estado\n'
		const csvRows = importableOrders.value.map((order) => {
			const [year, month, day] = order.date.split('-')
			const ddmmyyyy = `${day}/${month}/${year}`
			const amount = order.order_type === 'sell' ? -Math.abs(order.amount_eur) : order.amount_eur
			return `${ddmmyyyy};${order.isin};${amount};${order.shares};${order.status}`
		})

		const csvContent = csvHeader + csvRows.join('\n')
		const blob = new Blob([csvContent], { type: 'text/csv' })
		const file = new File([blob], 'orders.csv', { type: 'text/csv' })

		const formData = new FormData()
		formData.append('file', file)

		const token = localStorage.getItem('token')
		const response = await axios.post(`${API_BASE_URL}/api/orders/import-csv`, formData, {
			headers: {
				'Content-Type': 'multipart/form-data',
				Authorization: token ? `Bearer ${token}` : '',
			},
		})

		toastStore.addToast(
			`Successfully imported ${response.data.imported_count} orders and skipped ${response.data.skipped_count || 0}`,
			'success',
		)
		emit('imported', {
			imported_count: response.data.imported_count,
			rejected_count: response.data.rejected_count,
			skipped_count: response.data.skipped_count || 0,
		})
		close()
	} catch (error: any) {
		const message = error.response?.data?.detail || 'Failed to import orders'
		toastStore.addToast(message, 'error')
	} finally {
		importing.value = false
	}
}

function close() {
	emit('close')
	parsedOrders.value = []
	editingIndex.value = null
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
