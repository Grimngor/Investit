<template>
  <nav class="bg-white dark:bg-gray-800 shadow-md">
    <div class="container mx-auto px-4 py-4">
      <div class="flex justify-between items-center">
        <router-link to="/" class="text-2xl font-bold text-blue-600">
          Investit
        </router-link>
        
        <div class="flex items-center gap-4">
          <router-link
            v-if="!isAuthenticated"
            to="/login"
            class="text-gray-700 dark:text-gray-300 hover:text-blue-600"
          >
            Login
          </router-link>
          
          <router-link
            v-if="!isAuthenticated"
            to="/register"
            class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            Register
          </router-link>
          
          <router-link
            v-if="isAuthenticated"
            to="/portfolio"
            class="text-gray-700 dark:text-gray-300 hover:text-blue-600"
          >
            Portfolio
          </router-link>
          
          <button
            v-if="isAuthenticated"
            @click="handleLogout"
            class="text-gray-700 dark:text-gray-300 hover:text-red-600"
          >
            Logout
          </button>
          
          <ThemeToggle />
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import ThemeToggle from './ThemeToggle.vue'

const router = useRouter()
const authStore = useAuthStore()

const isAuthenticated = computed(() => authStore.isAuthenticated)

function handleLogout() {
  authStore.logout()
  router.push('/')
}
</script>
