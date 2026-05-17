<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
    @click.self="emit('close')"
  >
    <div
      class="m-4 flex max-h-[90vh] w-full max-w-5xl flex-col rounded-xl bg-white shadow-xl dark:bg-gray-800"
      role="dialog"
      aria-modal="true"
      aria-labelledby="gmail-import-title"
    >
      <div class="flex items-start justify-between gap-4 border-b border-gray-200 p-4 dark:border-gray-700 sm:p-6">
        <div>
          <h2 id="gmail-import-title" class="text-xl font-semibold text-gray-800 dark:text-gray-200">
            Import from Gmail
          </h2>
          <p v-if="status?.connected && status.email" class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {{ status.email }}
          </p>
        </div>
        <button
          @click="emit('close')"
          class="rounded p-1 text-gray-400 transition hover:text-gray-600 dark:hover:text-gray-300"
          aria-label="Close Gmail import"
        >
          <X class="h-6 w-6" />
        </button>
      </div>

      <div class="min-h-0 flex-1 overflow-y-auto p-4 sm:p-6">
        <div v-if="loadingStatus" class="py-8 text-center text-sm text-gray-500 dark:text-gray-400">
          Checking Gmail connection...
        </div>

        <div v-else-if="status && !status.configured" class="space-y-3">
          <p class="text-sm text-gray-700 dark:text-gray-300">Gmail import is not configured.</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            Set Google OAuth credentials on the backend before connecting Gmail.
          </p>
        </div>

        <div v-else-if="status && !status.connected" class="flex flex-col gap-4">
          <p class="text-sm text-gray-700 dark:text-gray-300">Connect Gmail to scan MyInvestor order emails.</p>
          <button @click="connectGmail" :disabled="connecting" class="gmail-primary-action self-start">
            <Link class="h-4 w-4" />
            {{ connecting ? 'Opening Google...' : 'Connect Gmail' }}
          </button>
        </div>

        <div v-else class="space-y-5">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div class="flex flex-wrap items-center gap-2">
              <button @click="scan" :disabled="scanning || importing" class="gmail-secondary-action">
                <Search class="h-4 w-4" />
                {{ scanning ? 'Scanning...' : 'Scan MyInvestor Emails' }}
              </button>
              <button
                @click="importSelected"
                :disabled="importing || selectedIds.length === 0"
                class="gmail-primary-action"
              >
                <Download class="h-4 w-4" />
                {{ importing ? 'Importing...' : `Import Selected (${selectedIds.length})` }}
              </button>
            </div>
            <button @click="disconnect" :disabled="scanning || importing" class="gmail-ghost-action">
              <Unlink class="h-4 w-4" />
              Disconnect
            </button>
          </div>

          <div v-if="scanResult" class="grid gap-3 text-sm sm:grid-cols-4">
            <div class="gmail-stat">
              <span class="text-gray-500 dark:text-gray-400">New</span>
              <strong>{{ scanResult.new_count }}</strong>
            </div>
            <div class="gmail-stat">
              <span class="text-gray-500 dark:text-gray-400">Already Present</span>
              <strong>{{ scanResult.skipped_count }}</strong>
            </div>
            <div class="gmail-stat">
              <span class="text-gray-500 dark:text-gray-400">Processed</span>
              <strong>{{ scanResult.already_processed_count }}</strong>
            </div>
            <div class="gmail-stat">
              <span class="text-gray-500 dark:text-gray-400">Review</span>
              <strong>{{ scanResult.needs_review_count }}</strong>
            </div>
          </div>

          <div v-if="scanResult?.errors.length" class="rounded-md border border-amber-300 bg-amber-50 p-3 text-xs text-amber-900 dark:border-amber-700 dark:bg-amber-900/20 dark:text-amber-200">
            <div v-for="error in scanResult.errors" :key="error">{{ error }}</div>
          </div>

          <div v-if="orders.length" class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
            <table class="min-w-full divide-y divide-gray-200 text-sm dark:divide-gray-700">
              <thead class="bg-gray-50 text-xs uppercase text-gray-500 dark:bg-gray-900/40 dark:text-gray-400">
                <tr>
                  <th class="w-10 px-3 py-3 text-left">
                    <input
                      type="checkbox"
                      :checked="allImportableSelected"
                      :disabled="importableOrders.length === 0"
                      @change="toggleAll"
                      class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  </th>
                  <th class="px-3 py-3 text-left">Date</th>
                  <th class="px-3 py-3 text-left">ISIN</th>
                  <th class="px-3 py-3 text-right">Amount</th>
                  <th class="px-3 py-3 text-right">Shares</th>
                  <th class="px-3 py-3 text-right">Price</th>
                  <th class="px-3 py-3 text-left">Status</th>
                  <th class="px-3 py-3 text-left">Existing Order</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
                <tr v-for="row in orders" :key="row.gmail_message_id">
                  <td class="px-3 py-3">
                    <input
                      type="checkbox"
                      :value="row.gmail_message_id"
                      v-model="selectedIds"
                      :disabled="row.import_status === 'already_present'"
                      class="rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:opacity-40"
                    />
                  </td>
                  <td class="whitespace-nowrap px-3 py-3 text-gray-700 dark:text-gray-300">{{ row.order.date }}</td>
                  <td class="whitespace-nowrap px-3 py-3 font-mono text-xs text-gray-700 dark:text-gray-300">
                    {{ row.order.isin }}
                  </td>
                  <td class="whitespace-nowrap px-3 py-3 text-right text-gray-700 dark:text-gray-300">
                    EUR {{ row.order.amount_eur.toFixed(2) }}
                  </td>
                  <td class="whitespace-nowrap px-3 py-3 text-right text-gray-700 dark:text-gray-300">
                    {{ row.order.shares }}
                  </td>
                  <td class="whitespace-nowrap px-3 py-3 text-right text-gray-700 dark:text-gray-300">
                    {{ row.unit_price.toFixed(4) }}
                  </td>
                  <td class="px-3 py-3">
                    <span :class="statusClass(row.import_status)">
                      {{ statusLabel(row.import_status) }}
                    </span>
                  </td>
                  <td class="px-3 py-3">
                    <div v-if="row.order.existing_order" class="space-y-0.5 text-xs text-gray-600 dark:text-gray-300">
                      <div class="font-mono">{{ row.order.existing_order.date }} - {{ row.order.existing_order.isin }}</div>
                      <div>
                        EUR {{ formatAmount(row.order.existing_order.amount_eur) }} / {{ row.order.existing_order.shares }} shares
                      </div>
                    </div>
                    <span v-else class="text-xs text-gray-400">-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-else-if="scanResult && !scanning" class="py-8 text-center text-sm text-gray-500 dark:text-gray-400">
            No importable MyInvestor orders found.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Download, Link, Search, Unlink, X } from 'lucide-vue-next'
import { apiClient, type GmailConnectionStatus, type GmailImportPreviewOrder, type GmailScanResponse } from '@/services/api'
import { useToastStore } from '@/stores/toast'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (event: 'close'): void
  (event: 'import-complete'): void
}>()

const toastStore = useToastStore()
const status = ref<GmailConnectionStatus | null>(null)
const scanResult = ref<GmailScanResponse | null>(null)
const selectedIds = ref<string[]>([])
const loadingStatus = ref(false)
const connecting = ref(false)
const scanning = ref(false)
const importing = ref(false)

const orders = computed(() => scanResult.value?.orders || [])
const importableOrders = computed(() => orders.value.filter((order) => order.import_status !== 'already_present'))
const defaultSelectedOrders = computed(() => orders.value.filter((order) => order.import_status === 'new'))
const allImportableSelected = computed(() => {
  return importableOrders.value.length > 0 && importableOrders.value.every((order) => selectedIds.value.includes(order.gmail_message_id))
})

watch(
  () => props.show,
  (show) => {
    if (show) {
      loadStatus()
    }
  },
)

async function loadStatus() {
  loadingStatus.value = true
  scanResult.value = null
  selectedIds.value = []
  try {
    status.value = await apiClient.getGmailStatus()
  } catch (error: any) {
    toastStore.addToast(error.response?.data?.detail || 'Failed to load Gmail status', 'error')
  } finally {
    loadingStatus.value = false
  }
}

async function connectGmail() {
  connecting.value = true
  try {
    const response = await apiClient.getGmailAuthUrl('/portfolio')
    window.location.href = response.auth_url
  } catch (error: any) {
    toastStore.addToast(error.response?.data?.detail || 'Failed to start Gmail connection', 'error')
    connecting.value = false
  }
}

async function disconnect() {
  try {
    await apiClient.disconnectGmail()
    toastStore.addToast('Gmail disconnected', 'success')
    await loadStatus()
  } catch (error: any) {
    toastStore.addToast(error.response?.data?.detail || 'Failed to disconnect Gmail', 'error')
  }
}

async function scan() {
  scanning.value = true
  selectedIds.value = []
  try {
    scanResult.value = await apiClient.scanGmailOrders()
    selectedIds.value = defaultSelectedOrders.value.map((order) => order.gmail_message_id)
    toastStore.addToast(`Found ${scanResult.value.new_count} new Gmail order(s)`, 'success')
  } catch (error: any) {
    toastStore.addToast(error.response?.data?.detail || 'Failed to scan Gmail', 'error')
  } finally {
    scanning.value = false
  }
}

async function importSelected() {
  importing.value = true
  try {
    const result = await apiClient.importGmailOrders(selectedIds.value)
    toastStore.addToast(result.message, result.error_count ? 'warning' : 'success')
    selectedIds.value = []
    await scan()
    emit('import-complete')
  } catch (error: any) {
    toastStore.addToast(error.response?.data?.detail || 'Failed to import Gmail orders', 'error')
  } finally {
    importing.value = false
  }
}

function toggleAll(event: Event) {
  const target = event.target as HTMLInputElement
  selectedIds.value = target.checked ? importableOrders.value.map((order) => order.gmail_message_id) : []
}

function statusLabel(statusValue: GmailImportPreviewOrder['import_status']) {
  if (statusValue === 'new') return 'New'
  if (statusValue === 'already_present') return 'Already present'
  if (statusValue === 'likely_duplicate') return 'Likely duplicate'
  if (statusValue === 'needs_review') return 'Needs review'
  return statusValue
}

function statusClass(statusValue: string) {
  const base = 'inline-flex rounded px-2 py-1 text-xs font-semibold whitespace-nowrap'
  if (statusValue === 'new') {
    return `${base} bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300`
  }
  if (statusValue === 'likely_duplicate') {
    return `${base} bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300`
  }
  if (statusValue === 'needs_review') {
    return `${base} bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300`
  }
  return `${base} bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300`
}

function formatAmount(value: number | undefined) {
  return Number(value || 0).toFixed(2)
}
</script>

<style scoped>
.gmail-primary-action,
.gmail-secondary-action,
.gmail-ghost-action {
  display: inline-flex;
  min-height: 2.375rem;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  border-radius: 0.375rem;
  border: 1px solid rgb(203 213 225);
  padding: 0.5rem 0.875rem;
  font-size: 0.875rem;
  font-weight: 500;
  transition:
    background-color 150ms ease,
    border-color 150ms ease,
    color 150ms ease,
    opacity 150ms ease;
}

.gmail-primary-action:disabled,
.gmail-secondary-action:disabled,
.gmail-ghost-action:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.gmail-primary-action {
  border-color: rgb(37 99 235);
  background-color: rgb(37 99 235);
  color: white;
}

.gmail-primary-action:hover:not(:disabled) {
  border-color: rgb(29 78 216);
  background-color: rgb(29 78 216);
}

.gmail-secondary-action,
.gmail-ghost-action {
  background-color: white;
  color: rgb(51 65 85);
}

.gmail-secondary-action:hover:not(:disabled),
.gmail-ghost-action:hover:not(:disabled) {
  border-color: rgb(148 163 184);
  background-color: rgb(248 250 252);
  color: rgb(15 23 42);
}

.gmail-stat {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-radius: 0.375rem;
  border: 1px solid rgb(226 232 240);
  padding: 0.75rem;
}

:global(.dark) .gmail-secondary-action,
:global(.dark) .gmail-ghost-action {
  border-color: rgb(75 85 99);
  background-color: rgb(31 41 55);
  color: rgb(229 231 235);
}

:global(.dark) .gmail-secondary-action:hover:not(:disabled),
:global(.dark) .gmail-ghost-action:hover:not(:disabled) {
  border-color: rgb(107 114 128);
  background-color: rgb(55 65 81);
  color: rgb(249 250 251);
}

:global(.dark) .gmail-stat {
  border-color: rgb(55 65 81);
}
</style>
