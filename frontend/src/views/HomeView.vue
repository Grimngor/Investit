<template>
  <AuthLayout subtitle="Access your portfolio">
    <template #title>Investit</template>
    <button
      v-if="authStore.googleAvailable"
      type="button"
      :disabled="googleLoading"
      class="w-full mb-4 inline-flex items-center justify-center gap-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2 text-sm font-medium text-gray-800 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
      @click="handleGoogleLogin"
    >
      <Mail class="h-4 w-4" aria-hidden="true" />
      {{ googleLoading ? 'Connecting...' : 'Continue with Google' }}
    </button>

    <button
      v-if="authStore.trustedProxyAvailable"
      type="button"
      :disabled="trustedProxyLoading"
      class="w-full mb-4 inline-flex items-center justify-center gap-2 rounded-lg border border-blue-200 dark:border-blue-800 bg-white dark:bg-gray-800 px-4 py-2 text-sm font-medium text-blue-700 dark:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 disabled:opacity-50 disabled:cursor-not-allowed"
      @click="handleTrustedProxyLogin"
    >
      <ShieldCheck class="h-4 w-4" aria-hidden="true" />
      {{ trustedProxyLoading ? 'Connecting...' : 'Continue with Tailscale' }}
    </button>

    <form @submit.prevent="handleLogin" class="space-y-4">
      <div>
        <label for="username" class="block text-sm font-medium mb-1">Username or email</label>
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
    <template #footer>
      Don't have an account?
      <router-link to="/register" class="text-blue-500 hover:underline font-medium"
        >Register</router-link
      >
    </template>
  </AuthLayout>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Mail, ShieldCheck } from 'lucide-vue-next'
import AuthLayout from '@/components/AuthLayout.vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const toastStore = useToastStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const trustedProxyLoading = ref(false)
const googleLoading = ref(false)

onMounted(async () => {
  await authStore.fetchAuthModes()
  await handleGoogleCallback()
})

async function handleLogin() {
  loading.value = true
  const success = await authStore.login(username.value, password.value)
  loading.value = false

  if (success) {
    router.push('/dashboard')
  }
}

async function handleTrustedProxyLogin() {
  trustedProxyLoading.value = true
  const success = await authStore.trustedProxyLogin()
  trustedProxyLoading.value = false

  if (success) {
    router.push('/dashboard')
  }
}

async function handleGoogleLogin() {
  googleLoading.value = true
  await authStore.startGoogleLogin('/')
  googleLoading.value = false
}

async function handleGoogleCallback() {
  const params = new URLSearchParams(route.hash.replace(/^#/, ''))
  const googleStatus = params.get('google')
  const accessToken = params.get('access_token')
  if (googleStatus === 'connected' && accessToken) {
    await authStore.completeExternalLogin(accessToken, 'Google login successful')
    await router.replace('/dashboard')
  } else if (googleStatus === 'error') {
    const message = params.get('message') || 'Google login failed'
    toastStore.addToast(message, 'error')
    await router.replace({ path: route.path, query: {}, hash: '' })
  }
}
</script>

<style scoped></style>
