<template>
  <div class="min-h-screen flex items-center justify-center px-4 py-12 bg-navy-900">
    <div class="max-w-md w-full">
      <h1 class="text-4xl font-bold mb-8 text-center text-blue-500">Login</h1>
      <AuthCard>
        <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label for="username" class="block text-sm font-medium mb-1">Username</label>
            <input id="username" v-model="username" type="text" required class="input-base" />
        </div>

        <div>
          <label for="password" class="block text-sm font-medium mb-1">Password</label>
            <input id="password" v-model="password" type="password" required class="input-base" />
        </div>

          <button type="submit" :disabled="loading" class="btn-primary w-full">
            {{ loading ? 'Logging in...' : 'Login' }}
          </button>
        </form>
      </AuthCard>

      <p class="mt-4 text-center text-gray-500 dark:text-gray-400 text-sm">
        Don't have an account?
        <router-link to="/register" class="text-blue-500 hover:underline font-medium">Register</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AuthCard from '@/components/AuthCard.vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)

async function handleLogin() {
  loading.value = true
  const success = await authStore.login(username.value, password.value)
  loading.value = false

  if (success) {
    router.push('/portfolio')
  }
}
</script>
