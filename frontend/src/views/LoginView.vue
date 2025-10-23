<template>
  <AuthLayout subtitle="Welcome back">
    <template #title>Login</template>
    <form @submit.prevent="handleLogin" class="space-y-4">
      <div>
        <label for="username" class="block text-sm font-medium mb-1">Username</label>
        <input id="username" v-model="username" type="text" required class="input-base" />
      </div>
      <div>
        <label for="password" class="block text-sm font-medium mb-1">Password</label>
        <input id="password" v-model="password" type="password" required class="input-base" />
      </div>
      <button type="submit" :disabled="loading" class="btn-primary w-full">{{ loading ? 'Logging in...' : 'Login' }}</button>
    </form>
    <template #footer>
      Don't have an account?
      <router-link to="/register" class="text-blue-500 hover:underline font-medium">Register</router-link>
    </template>
  </AuthLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AuthLayout from '@/components/AuthLayout.vue'
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
    router.push('/dashboard')
  }
}
</script>
