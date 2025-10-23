<template>
  <div class="fixed top-4 right-4 z-50 space-y-2">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      :class="toastClass(toast.type)"
      class="px-4 py-3 rounded-md shadow-lg min-w-[300px] animate-slide-in"
    >
      <div class="flex justify-between items-start gap-4">
        <p class="text-sm">{{ toast.message }}</p>
        <button
          @click="removeToast(toast.id)"
          class="text-white hover:text-gray-200 flex-shrink-0"
        >
          ×
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useToastStore, type Toast } from '@/stores/toast'

const toastStore = useToastStore()

const toasts = computed(() => toastStore.toasts)

function toastClass(type: Toast['type']): string {
  const baseClass = 'text-white '
  switch (type) {
    case 'success':
      return baseClass + 'bg-green-600'
    case 'error':
      return baseClass + 'bg-red-600'
    case 'warning':
      return baseClass + 'bg-yellow-600'
    case 'info':
      return baseClass + 'bg-blue-600'
    default:
      return baseClass + 'bg-gray-600'
  }
}

function removeToast(id: number) {
  toastStore.removeToast(id)
}
</script>

<style scoped>
@keyframes slide-in {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.animate-slide-in {
  animation: slide-in 0.3s ease-out;
}
</style>
