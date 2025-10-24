<template>
  <div
    class="rounded-xl border border-softblue-200 dark:border-gray-700 bg-white dark:bg-gray-800/60 backdrop-blur p-6 shadow-sm"
  >
    <h2 class="text-lg font-semibold mb-4 text-gray-800 dark:text-gray-200">
      Import Orders from CSV
    </h2>
    <p class="text-sm text-gray-600 dark:text-gray-400 mb-6">
      Upload your bank CSV file with order history. Expected format: Spanish bank CSV (Fecha de la
      orden, ISIN, Importe estimado, Nº de participaciones, Estado). Supports both comma and
      semicolon delimiters.
    </p>

    <!-- File Drop Zone -->
    <div
      @drop.prevent="handleDrop"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      :class="[
        'border-2 border-dashed rounded-lg p-8 text-center transition-all cursor-pointer',
        isDragging
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
          : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500',
      ]"
      @click="triggerFileInput"
    >
      <input ref="fileInput" type="file" accept=".csv" @change="handleFileSelect" class="hidden" />

      <div class="flex flex-col items-center gap-3">
        <svg class="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
        <div>
          <p class="text-sm font-medium text-gray-700 dark:text-gray-300">
            Drop your CSV file here or click to browse
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Only .csv files are accepted</p>
        </div>
      </div>

      <div
        v-if="selectedFile"
        class="mt-4 flex items-center justify-center gap-2 text-sm text-blue-600 dark:text-blue-400"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <span class="font-medium">{{ selectedFile.name }}</span>
      </div>
    </div>

    <!-- Upload Button -->
    <div class="mt-6 flex justify-end gap-3">
      <button
        v-if="selectedFile"
        @click="clearFile"
        :disabled="uploading"
        class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition disabled:opacity-50"
      >
        Clear
      </button>
      <button
        @click="uploadFile"
        :disabled="!selectedFile || uploading"
        class="px-6 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
      >
        <svg v-if="uploading" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
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
        <span>{{ uploading ? 'Uploading...' : 'Upload & Import' }}</span>
      </button>
    </div>

    <!-- Results Section -->
    <div v-if="importResult" class="mt-6 space-y-4">
      <!-- Success Summary -->
      <div
        v-if="importResult.imported_count > 0"
        class="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg"
      >
        <div class="flex items-center gap-2">
          <svg
            class="w-5 h-5 text-green-600 dark:text-green-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span class="font-medium text-green-800 dark:text-green-200">
            Successfully imported {{ importResult.imported_count }} order{{
              importResult.imported_count > 1 ? 's' : ''
            }}
          </span>
        </div>
      </div>

      <!-- Rejected Summary -->
      <div
        v-if="importResult.rejected_count > 0"
        class="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg"
      >
        <div class="flex items-center gap-2">
          <svg
            class="w-5 h-5 text-amber-600 dark:text-amber-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <span class="font-medium text-amber-800 dark:text-amber-200">
            Skipped {{ importResult.rejected_count }} rejected order{{
              importResult.rejected_count > 1 ? 's' : ''
            }}
          </span>
        </div>
      </div>

      <!-- Errors -->
      <div
        v-if="importResult.errors && importResult.errors.length > 0"
        class="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
      >
        <div class="flex items-start gap-2 mb-3">
          <svg
            class="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div class="flex-1">
            <span class="font-medium text-red-800 dark:text-red-200 block mb-2">
              {{ importResult.errors.length }} error{{
                importResult.errors.length > 1 ? 's' : ''
              }}
              encountered
            </span>
            <div class="space-y-1 text-sm text-red-700 dark:text-red-300">
              <div v-for="(error, idx) in importResult.errors" :key="idx">
                <span>{{ error }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'
import { useToastStore } from '@/stores/toast'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface ImportResult {
  imported_count: number
  rejected_count: number
  errors?: Array<{ row: number; error: string }>
}

const emit = defineEmits<{
  (e: 'import-complete'): void
}>()

const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const isDragging = ref(false)
const uploading = ref(false)
const importResult = ref<ImportResult | null>(null)
const toastStore = useToastStore()

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
    importResult.value = null
  }
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
    const file = event.dataTransfer.files[0]
    if (file.name.endsWith('.csv')) {
      selectedFile.value = file
      importResult.value = null
    } else {
      toastStore.addToast('Please select a CSV file', 'error')
    }
  }
}

function clearFile() {
  selectedFile.value = null
  importResult.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

async function uploadFile() {
  if (!selectedFile.value) return

  uploading.value = true
  importResult.value = null

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)

    const token = localStorage.getItem('token')
    const response = await axios.post(`${API_BASE_URL}/api/orders/import-csv`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        Authorization: token ? `Bearer ${token}` : '',
      },
    })

    importResult.value = response.data

    if (response.data.imported_count > 0) {
      toastStore.addToast(`Successfully imported ${response.data.imported_count} orders`, 'success')
      emit('import-complete')
    }

    if (response.data.errors && response.data.errors.length === 0) {
      clearFile()
    }
  } catch (error: any) {
    const message = error.response?.data?.detail || 'Failed to import CSV'
    toastStore.addToast(message, 'error')
    console.error('CSV import error:', error)
  } finally {
    uploading.value = false
  }
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
