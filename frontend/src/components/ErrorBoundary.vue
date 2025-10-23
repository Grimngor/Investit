<template>
  <div v-if="hasError" class="error-boundary">
    <Card class="max-w-lg mx-auto">
      <template #header>
        <div class="flex items-center gap-2 text-destructive">
          <AlertTriangle class="h-5 w-5" />
          <h3 class="text-lg font-semibold">Something went wrong</h3>
        </div>
      </template>

      <div class="space-y-4">
        <p class="text-muted-foreground">
          {{ fallbackMessage || 'An unexpected error occurred. Please try again.' }}
        </p>

        <div v-if="showDetails && error" class="space-y-2">
          <Button
            variant="outline"
            size="sm"
            @click="showErrorDetails = !showErrorDetails"
            class="text-xs"
          >
            {{ showErrorDetails ? 'Hide' : 'Show' }} Error Details
          </Button>

          <div v-if="showErrorDetails" class="p-3 bg-muted rounded-md">
            <pre class="text-xs text-muted-foreground whitespace-pre-wrap">{{ formatError(error) }}</pre>
          </div>
        </div>

        <div class="flex gap-2">
          <Button @click="retry" variant="default">
            <RotateCcw class="h-4 w-4 mr-2" />
            Try Again
          </Button>
          
          <Button @click="goHome" variant="outline">
            <Home class="h-4 w-4 mr-2" />
            Go Home
          </Button>

          <Button
            v-if="onReport"
            @click="reportError"
            variant="outline"
            size="sm"
          >
            <Bug class="h-4 w-4 mr-2" />
            Report Issue
          </Button>
        </div>
      </div>
    </Card>
  </div>

  <slot v-else />
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'
import { useRouter } from 'vue-router'
import { AlertTriangle, RotateCcw, Home, Bug } from 'lucide-vue-next'
import Card from './ui/Card.vue'
import Button from './ui/Button.vue'

interface Props {
  fallbackMessage?: string
  showDetails?: boolean
  onReport?: () => void
}

const props = withDefaults(defineProps<Props>(), {
  fallbackMessage: '',
  showDetails: true,
})

const router = useRouter()
const hasError = ref(false)
const error = ref<Error | null>(null)
const showErrorDetails = ref(false)

onErrorCaptured((err: Error) => {
  hasError.value = true
  error.value = err
  console.error('Error boundary caught:', err)
  return false // Prevent error from propagating
})

function formatError(err: Error): string {
  return `${err.name}: ${err.message}\n\n${err.stack || 'No stack trace available'}`
}

function retry() {
  hasError.value = false
  error.value = null
  showErrorDetails.value = false
  // Optionally, you can emit an event or call a method to retry the failed operation
}

function goHome() {
  hasError.value = false
  error.value = null
  router.push('/')
}

function reportError() {
  if (props.onReport) {
    props.onReport()
  }
}
</script>
