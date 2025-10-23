<template>
  <nav class="sticky top-0 z-40 backdrop-blur bg-softblue-50/80 dark:bg-navy-800/70 border-b border-softblue-200 dark:border-gray-700">
    <div class="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between">
  <router-link :to="logoTarget" class="text-xl font-bold text-blue-600 dark:text-blue-400">Investit</router-link>
      <div class="flex items-center gap-6">
  <router-link v-if="isAuthenticated" to="/dashboard" class="nav-link" :class="{ active: isRoute('/dashboard') }">Dashboard</router-link>
        <router-link v-if="isAuthenticated" to="/portfolio" class="nav-link" :class="{ active: isRoute('/portfolio') }">Portfolio</router-link>
        <router-link v-if="isAuthenticated" to="/orders" class="nav-link" :class="{ active: isRoute('/orders') }">Orders</router-link>
        <router-link v-if="!isAuthenticated" to="/login" class="nav-link" :class="{ active: isRoute('/login') }">Login</router-link>
        <router-link v-if="!isAuthenticated" to="/register" class="px-4 py-2 rounded-md bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium">Register</router-link>
        <button v-if="isAuthenticated" @click="handleLogout" class="text-xs text-gray-600 dark:text-gray-300 hover:text-red-600">Logout</button>
        <ThemeToggle />
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import ThemeToggle from './ThemeToggle.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isAuthenticated = computed(() => authStore.isAuthenticated)
const logoTarget = computed(() => (isAuthenticated.value ? '/dashboard' : '/'))

function handleLogout() {
  authStore.logout()
  router.push('/')
}

function isRoute(path: string): boolean { return route.path === path }
</script>
