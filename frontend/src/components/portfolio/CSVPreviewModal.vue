<template>
	<Teleport to="body">
		<div
			v-if="isOpen"
			class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm"
			@click.self="close"
		>
			<div
				class="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-6xl max-h-[90vh] overflow-hidden m-4 flex flex-col"
			>
				<!-- Header -->
				<div
					class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700"
				>
					<div>
						<h2 class="text-xl font-semibold text-gray-800 dark:text-gray-200">
							Preview & Edit CSV Import
						</h2>
						<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
							Review {{ parsedOrders.length }} orders before importing
						</p>
				</div>
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

			<!-- Table container with scroll -->
			<div class="flex-1 overflow-auto p-6">
				<table class="w-full text-sm border border-gray-200 dark:border-gray-700 rounded-lg">
					<thead class="bg-gray-100 dark:bg-gray-800 sticky top-0">
						<tr>
							<th class="px-3 py-2 text-left text-xs font-medium">#</th>
							<th class="px-3 py-2 text-left text-xs font-medium">Date</th>
							<th class="px-3 py-2 text-left text-xs font-medium">ISIN</th>
							<th class="px-3 py-2 text-left text-xs font-medium">Amount (EUR)</th>
							<th class="px-3 py-2 text-left text-xs font-medium">Shares</th>
							<th class="px-3 py-2 text-left text-xs font-medium">Status</th>
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
									: 'hover:bg-gray-50 dark:hover:bg-gray-700/40'
							]"
						>
							<!-- Row Number -->
							<td class="px-3 py-2 text-gray-500 dark:text-gray-400 text-xs">{{ idx + 1 }}</td>

							<!-- Date -->
							<td class="px-3 py-2">
								<input
									v-if="editingIndex === idx"
									v-model="editForm.date"
									type="date"
									class="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200"
								/>
								<span v-else class="text-xs">{{ order.date }}</span>
							</td>

							<!-- ISIN -->
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

							<!-- Amount -->
							<td class="px-3 py-2">
								<input
									v-if="editingIndex === idx"
									v-model.number="editForm.amount_eur"
									type="number"
									step="0.01"
									class="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-200"
								/>
								<span v-else class="text-xs">€{{ order.amount_eur?.toFixed(2) }}</span>
							</td>

							<!-- Shares -->
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

							<!-- Status -->
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
											: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
									]"
								>
									{{ order.status }}
								</span>
							</td>

							<!-- Actions -->
							<td class="px-3 py-2">
								<div v-if="editingIndex === idx" class="flex gap-1 justify-center">
									<button
										@click="saveEdit(idx)"
										class="p-1 text-green-600 hover:bg-green-50 dark:text-green-400 dark:hover:bg-green-900/20 rounded"
										title="Save"
									>
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M5 13l4 4L19 7"
											/>
										</svg>
									</button>
									<button
										@click="cancelEdit"
										class="p-1 text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-gray-700 rounded"
										title="Cancel"
									>
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M6 18L18 6M6 6l12 12"
											/>
										</svg>
									</button>
								</div>
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

				<div v-if="parsedOrders.length === 0" class="text-center py-12 text-gray-400">
					No valid orders found in CSV
				</div>
			</div>

			<!-- Footer -->
			<div
				class="flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/30"
			>
				<div class="text-sm text-gray-600 dark:text-gray-400">
					<span class="font-medium text-gray-800 dark:text-gray-200">{{
						parsedOrders.length
					}}</span>
					orders ready to import
				</div>
				<div class="flex gap-3">
					<button
						@click="close"
						:disabled="importing"
						class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 border border-gray-300 dark:border-gray-600 rounded-lg transition disabled:opacity-50"
					>
						Cancel
					</button>
					<button
						@click="handleImport"
						:disabled="importing || parsedOrders.length === 0"
						class="px-6 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
					>
						<svg
							v-if="importing"
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
						<span>{{ importing ? 'Importing...' : 'Import Orders' }}</span>
					</button>
				</div>
			</div>
		</div>
	</div>
	</Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import axios from 'axios'
import { useToastStore } from '@/stores/toast'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface CSVOrder {
	date: string
	isin: string
	amount_eur: number
	shares: number
	status: string
}

interface Props {
	file: File | null
	isOpen: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
	(e: 'close'): void
	(e: 'imported', result: { imported_count: number; rejected_count: number }): void
}>()

const toastStore = useToastStore()
const parsedOrders = ref<CSVOrder[]>([])
const importing = ref(false)
const editingIndex = ref<number | null>(null)
const editForm = ref<CSVOrder>({
	date: '',
	isin: '',
	amount_eur: 0,
	shares: 0,
	status: 'Finalizada'
})

// Parse CSV when file changes or modal opens
watch(
	() => [props.file, props.isOpen] as const,
	async ([newFile, isOpen]) => {
		if (newFile && isOpen) {
			console.log('Parsing CSV file:', newFile.name)
			await parseCSV(newFile)
		}
	},
	{ immediate: true }
)

async function parseCSV(file: File) {
	try {
		const text = await file.text()
		const lines = text
			.split('\n')
			.map((l) => l.trim())
			.filter((l) => l.length > 0)

		if (lines.length === 0) {
			toastStore.addToast('CSV file is empty', 'error')
			return
		}

		// Auto-detect delimiter (comma or semicolon)
		const delimiter = lines[0].includes(';') ? ';' : ','
		const headers = lines[0].split(delimiter).map((h) => h.trim().replace(/"/g, ''))

		console.log('CSV Headers:', headers)
		console.log('Delimiter:', delimiter)

	// Check if it's a crypto exchange CSV
	const isCryptoCsv =
		headers.some((h) => h.includes('Date(UTC')) &&
		headers.some((h) => h.includes('Spend Amount')) &&
		headers.some((h) => h.includes('Receive Amount'))

	if (isCryptoCsv) {
		// Parse crypto CSV for preview
		console.log('Detected crypto exchange CSV - parsing for preview')

		// Expected columns: Date(UTC+1), Method, Spend Amount, Receive Amount, Fee, Price, Status, Transaction ID
		const dateIdx = headers.findIndex((h) => h.includes('Date(UTC'))
		const spendIdx = headers.findIndex((h) => h.includes('Spend Amount'))
		const receiveIdx = headers.findIndex((h) => h.includes('Receive Amount'))
		const feeIdx = headers.findIndex((h) => h.includes('Fee'))
		const statusIdx = headers.findIndex((h) => h.includes('Status'))

		for (let i = 1; i < lines.length; i++) {
			const row = lines[i].split(delimiter).map((cell) => cell.trim().replace(/"/g, ''))

			if (row.length < 8 || !row[dateIdx] || !row[spendIdx]) {
				continue // Skip empty or invalid rows
			}

			try {
				// Parse date (DD/MM/YYYY HH:MM or YYYY-MM-DD HH:MM:SS)
				const dateStr = row[dateIdx].split(' ')[0] // Get date part
				let parsedDate: Date
				if (dateStr.includes('/')) {
					const [day, month, year] = dateStr.split('/')
					parsedDate = new Date(parseInt(year), parseInt(month) - 1, parseInt(day))
				} else {
					parsedDate = new Date(dateStr)
				}
				const isoDate = parsedDate.toISOString().split('T')[0]

				// Parse spend amount (e.g., "50.00 EUR")
				const spendParts = row[spendIdx].split(' ')
				const amountEur = parseFloat(spendParts[0])

				// Parse receive amount (e.g., "0.00279397 BTC")
				const receiveParts = row[receiveIdx].split(' ')
				const shares = parseFloat(receiveParts[0])
				const symbol = receiveParts[1] || 'UNKNOWN'

				// Parse status
				const status = row[statusIdx].toLowerCase().includes('success') ? 'Finalizada' : 'Rechazada'

				parsedOrders.value.push({
					date: isoDate,
					isin: symbol.toUpperCase(),
					amount_eur: amountEur,
					shares: shares,
					status: status
				})
			} catch (error) {
				console.error(`Error parsing crypto CSV row ${i}:`, error)
				continue
			}
		}

		toastStore.addToast(`Parsed ${parsedOrders.value.length} crypto transactions`, 'success')
		return
	}		// Expected Spanish bank columns: Fecha de la orden, ISIN, Importe estimado, Nº de participaciones, Estado
		const dateIdx = headers.findIndex((h) => h.toLowerCase().includes('fecha'))
		const isinIdx = headers.findIndex((h) => h.toUpperCase() === 'ISIN')
		const amountIdx = headers.findIndex((h) => h.toLowerCase().includes('importe'))
		const sharesIdx = headers.findIndex((h) => h.toLowerCase().includes('participacion'))
		const statusIdx = headers.findIndex((h) => h.toLowerCase().includes('estado'))

		console.log('Column indices:', { dateIdx, isinIdx, amountIdx, sharesIdx, statusIdx })

		if (dateIdx === -1 || isinIdx === -1 || amountIdx === -1 || sharesIdx === -1) {
			toastStore.addToast('Invalid CSV format. Missing required columns.', 'error')
			console.error('Missing columns. Headers:', headers)
			return
		}

		const orders: CSVOrder[] = []

		for (let i = 1; i < lines.length; i++) {
			const cols = lines[i].split(delimiter).map((c) => c.trim().replace(/"/g, ''))

			if (cols.length < Math.max(dateIdx, isinIdx, amountIdx, sharesIdx) + 1) {
				console.warn(`Row ${i} skipped - insufficient columns:`, cols)
				continue // Skip malformed rows
			}

			const date = convertToISODate(cols[dateIdx])
			const isin = cols[isinIdx].trim()
			const amountStr = cols[amountIdx].replace(/[^\d,.-]/g, '').replace(',', '.')
			const sharesStr = cols[sharesIdx].replace(/[^\d,.-]/g, '').replace(',', '.')
			const status = statusIdx !== -1 ? cols[statusIdx] : 'Finalizada'

			const amount = parseFloat(amountStr)
			const shares = parseFloat(sharesStr)

			console.log(`Row ${i}:`, { date, isin, amount, shares, status })

			if (isin.length === 12 && !isNaN(amount) && !isNaN(shares) && amount !== 0 && shares !== 0) {
				orders.push({
					date,
					isin,
					amount_eur: amount,
					shares,
					status: status || 'Finalizada'
				})
			} else {
				console.warn(`Row ${i} validation failed:`, {
					isinLength: isin.length,
					amount,
					shares,
					amountValid: !isNaN(amount) && amount !== 0,
					sharesValid: !isNaN(shares) && shares !== 0
				})
			}
		}

		console.log('Parsed orders:', orders)
		parsedOrders.value = orders

		if (orders.length === 0) {
			toastStore.addToast('No valid orders found in CSV', 'warning')
		}
	} catch (error) {
		console.error('CSV parsing error:', error)
		toastStore.addToast('Failed to parse CSV file', 'error')
	}
}

// Convert DD/MM/YYYY to YYYY-MM-DD
function convertToISODate(ddmmyyyy: string): string {
	const parts = ddmmyyyy.split('/')
	if (parts.length === 3) {
		const [day, month, year] = parts
		return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`
	}
	return ddmmyyyy
}

function startEdit(idx: number, order: CSVOrder) {
	editingIndex.value = idx
	editForm.value = { ...order }
}

function saveEdit(idx: number) {
	parsedOrders.value[idx] = { ...editForm.value }
	editingIndex.value = null
}

function cancelEdit() {
	editingIndex.value = null
}

function removeOrder(idx: number) {
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
				Authorization: token ? `Bearer ${token}` : ''
			}
		})

		toastStore.addToast(
			`Successfully imported ${response.data.imported_count} crypto orders`,
			'success'
		)
		emit('imported', {
			imported_count: response.data.imported_count,
			rejected_count: response.data.rejected_count
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
	if (parsedOrders.value.length === 0) return

	// Check if these are crypto orders (symbol length 3-5 chars)
	const isCryptoOrders = parsedOrders.value.every(
		(order) => order.isin && order.isin.length >= 3 && order.isin.length <= 5
	)

	if (isCryptoOrders && props.file) {
		// Import the original file directly for crypto
		await handleCryptoImport(props.file)
		return
	}

	importing.value = true
	try {
		// Convert back to CSV format and submit
		const csvHeader = 'Fecha de la orden;ISIN;Importe estimado;Nº de participaciones;Estado\n'
		const csvRows = parsedOrders.value.map((order) => {
			// Convert YYYY-MM-DD back to DD/MM/YYYY
			const [year, month, day] = order.date.split('-')
			const ddmmyyyy = `${day}/${month}/${year}`
			return `${ddmmyyyy};${order.isin};${order.amount_eur};${order.shares};${order.status}`
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
				Authorization: token ? `Bearer ${token}` : ''
			}
		})

		toastStore.addToast(
			`Successfully imported ${response.data.imported_count} orders`,
			'success'
		)
		emit('imported', {
			imported_count: response.data.imported_count,
			rejected_count: response.data.rejected_count
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
