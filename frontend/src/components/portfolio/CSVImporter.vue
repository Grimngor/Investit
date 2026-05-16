<template>
  <div :class="containerClasses">
    <h2 v-if="showTitle" class="text-lg font-semibold mb-4 text-gray-800 dark:text-gray-200">
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
        class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition"
      >
        Clear
      </button>
      <button
        @click="openPreview"
        :disabled="!selectedFile"
        class="px-6 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
      >
        <span>Preview & Import</span>
      </button>
    </div>

    <!-- CSV Preview Modal -->
    <CSVPreviewModal
      :file="selectedFile"
      :is-open="showPreview"
      @close="closePreview"
      @imported="handleImported"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useToastStore } from '@/stores/toast'
import CSVPreviewModal from './CSVPreviewModal.vue'

interface ImportResult {
  imported_count: number
  rejected_count: number
  skipped_count?: number
  errors?: Array<{ row: number; error: string }>
}

const emit = defineEmits<{
  (e: 'import-complete'): void
}>()

interface Props {
  embedded?: boolean
  showTitle?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  embedded: false,
  showTitle: true,
})

const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const isDragging = ref(false)
const toastStore = useToastStore()
const showPreview = ref(false)
const containerClasses = computed(() =>
  props.embedded
    ? ''
    : 'rounded-xl border border-softblue-200 dark:border-gray-700 bg-white dark:bg-gray-800/60 backdrop-blur p-6 shadow-sm',
)

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
  }
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
    const file = event.dataTransfer.files[0]
    if (file.name.endsWith('.csv')) {
      selectedFile.value = file
    } else {
      toastStore.addToast('Please select a CSV file', 'error')
    }
  }
}

function clearFile() {
  selectedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

function openPreview() {
  if (selectedFile.value) {
    showPreview.value = true
  }
}

function closePreview() {
  showPreview.value = false
}

function handleImported(result: ImportResult) {
  emit('import-complete')
  clearFile()
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
