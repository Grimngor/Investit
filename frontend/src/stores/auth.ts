import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { apiClient } from '@/services/api'
import { wsClient } from '@/services/websocket'
import { useToastStore } from './toast'
import { logger } from '@/utils/logger'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<any>(null)
  const token = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(username: string, password: string) {
    loading.value = true
    error.value = null

    try {
      const data = await apiClient.login(username, password)

      token.value = data.access_token
      localStorage.setItem('token', data.access_token)

      // Fetch user info
      await loadUser()

      // Connect WebSocket with duplicate connection guard
      const ws = (wsClient as any).ws
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        wsClient.connect(data.access_token)
      }

      useToastStore().addToast('Login successful', 'success')

      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Login failed'
      useToastStore().addToast(error.value, 'error')
      return false
    } finally {
      loading.value = false
    }
  }

  async function register(userData: { username: string; email: string; password: string; full_name?: string }) {
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
        const ws = (wsClient as any).ws
        if (!ws || ws.readyState !== WebSocket.OPEN) {
          wsClient.connect(storedToken)
        }
      }
    } catch (err) {
      logger.error('Failed to load user', { error: err })
      logout()
    }
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    wsClient.disconnect()
    useToastStore().addToast('Logged out successfully', 'info')
  }

  function initializeAuth() {
    const storedToken = localStorage.getItem('token')
    const storedUser = localStorage.getItem('user')

    if (storedToken && storedUser) {
      token.value = storedToken
      user.value = JSON.parse(storedUser)
      loadUser()
    }
  }

  return {
    user,
    token,
    loading,
    error,
    isAuthenticated,
    login,
    register,
    logout,
    loadUser,
    initializeAuth
  }
})
