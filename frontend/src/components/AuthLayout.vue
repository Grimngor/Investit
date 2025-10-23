<template>
  <div class="min-h-screen flex items-center justify-center px-4 py-12 bg-gradient-to-br from-navy-900 to-black">
    <div class="w-full max-w-md space-y-6">
      <header class="text-center space-y-2">
        <h1 class="text-5xl font-bold tracking-tight text-blue-500">
          <slot name="title" />
        </h1>
        <p v-if="subtitle" class="text-xs text-gray-500 dark:text-gray-400">{{ subtitle }}</p>
      </header>
      <AuthCard :customClass="'space-y-6'">
        <slot />
      </AuthCard>
      <footer class="text-center text-xs text-gray-500 dark:text-gray-400">
        <slot name="footer" />
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import AuthCard from './AuthCard.vue'
defineProps<{ subtitle?: string }>()
</script>

<style scoped></style>
