import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { apiClient, type AuthModes } from '@/services/api'
import { wsClient } from '@/services/websocket'
import { useToastStore } from './toast'
import { logger } from '@/utils/logger'

const DEFAULT_AUTH_MODES: AuthModes = {
  password: true,
  trusted_proxy: false,
  google: false,
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<any>(null)
  const token = ref<string | null>(null)
  const authModes = ref<AuthModes>({ ...DEFAULT_AUTH_MODES })
  const loading = ref(false)
  const error = ref<string | null>(null)
  const trustedProxyAttempted = ref(false)

  const isAuthenticated = computed(() => !!token.value)
  const trustedProxyAvailable = computed(() => authModes.value.trusted_proxy)
  const googleAvailable = computed(() => authModes.value.google)

  function connectWebSocket(accessToken: string) {
    const ws = (wsClient as any).ws
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      wsClient.connect(accessToken)
    }
  }

  async function completeLogin(accessToken: string, toastMessage?: string) {
    token.value = accessToken
    localStorage.setItem('token', accessToken)

    await loadUser()
    connectWebSocket(accessToken)

    apiClient.refreshPricesIfNeeded().catch((err) => {
      logger.warn('Price refresh check after login failed', { error: err })
    })

    if (toastMessage) {
      useToastStore().addToast(toastMessage, 'success')
    }
  }

  async function fetchAuthModes() {
    try {
      authModes.value = await apiClient.getAuthModes()
      return authModes.value
    } catch (err) {
      logger.warn('Failed to load auth modes', { error: err })
      authModes.value = { ...DEFAULT_AUTH_MODES }
      return authModes.value
    }
  }

  async function login(username: string, password: string) {
    loading.value = true
    error.value = null

    try {
      const data = await apiClient.login(username, password)
      await completeLogin(data.access_token, 'Login successful')

      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Login failed'
      useToastStore().addToast(error.value, 'error')
      return false
    } finally {
      loading.value = false
    }
  }

  async function trustedProxyLogin(showToast = true) {
    loading.value = true
    error.value = null

    try {
      const data = await apiClient.trustedProxyLogin()
      await completeLogin(data.access_token, showToast ? 'Tailscale login successful' : undefined)
      return true
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Tailscale login failed'
      if (showToast) {
        error.value = message
        useToastStore().addToast(message, 'error')
      }
      return false
    } finally {
      loading.value = false
    }
  }

  async function startGoogleLogin(returnPath = '/dashboard') {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.getGoogleAuthUrl(returnPath)
      window.location.href = response.auth_url
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Google login failed'
      useToastStore().addToast(error.value, 'error')
      return false
    } finally {
      loading.value = false
    }
  }

  async function completeExternalLogin(accessToken: string, toastMessage?: string) {
    await completeLogin(accessToken, toastMessage)
    return true
  }

  async function tryTrustedProxyLogin() {
    if (isAuthenticated.value || trustedProxyAttempted.value) {
      return isAuthenticated.value
    }

    trustedProxyAttempted.value = true
    const modes = await fetchAuthModes()
    if (!modes.trusted_proxy) {
      return false
    }

    return trustedProxyLogin(false)
  }

  async function register(userData: {
    email: string
    username?: string
    password: string
    full_name?: string
  }) {
    loading.value = true
    error.value = null

    try {
      await apiClient.register(userData)
      useToastStore().addToast('Registration successful! Please login.', 'success')
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Registration failed'
      useToastStore().addToast(error.value, 'error')
      return false
    } finally {
      loading.value = false
    }
  }

  async function loadUser() {
    try {
      user.value = await apiClient.getCurrentUser()
      localStorage.setItem('user', JSON.stringify(user.value))

      // Connect WebSocket if we have a token and not already connected
      const storedToken = localStorage.getItem('token')
      if (storedToken) {
        connectWebSocket(storedToken)
      }
      return true
    } catch (err) {
      logger.error('Failed to load user', { error: err })
      return false
    }
  }

  function logout() {
    user.value = null
    token.value = null
    trustedProxyAttempted.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    wsClient.disconnect()
    void fetchAuthModes()
    useToastStore().addToast('Logged out successfully', 'info')
  }

  function initializeAuth() {
    const storedToken = localStorage.getItem('token')
    const storedUser = localStorage.getItem('user')

    if (storedToken) {
      token.value = storedToken
    }

    if (storedUser) {
      user.value = JSON.parse(storedUser)
    }

    if (storedToken) {
      connectWebSocket(storedToken)
    }
  }

  return {
    user,
    token,
    authModes,
    loading,
    error,
    isAuthenticated,
    trustedProxyAvailable,
    googleAvailable,
    login,
    trustedProxyLogin,
    startGoogleLogin,
    completeExternalLogin,
    tryTrustedProxyLogin,
    register,
    fetchAuthModes,
    logout,
    loadUser,
    initializeAuth,
  }
})
