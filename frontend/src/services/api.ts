import axios, { type AxiosInstance } from 'axios'
import { API_BASE_URL } from '@/services/config'

export interface AuthModes {
  password: boolean
  trusted_proxy: boolean
}

class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add request interceptor to include auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error),
    )

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        const requestUrl = error.config?.url || ''
        if (error.response?.status === 401 && !requestUrl.includes('/api/auth/login')) {
          // Token expired or invalid
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      },
    )
  }

  // Auth endpoints
  async login(username: string, password: string) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const response = await this.client.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return response.data
  }

  async getAuthModes(): Promise<AuthModes> {
    const response = await this.client.get('/api/auth/modes')
    return response.data
  }

  async trustedProxyLogin() {
    const response = await this.client.post('/api/auth/trusted-proxy/login')
    return response.data
  }

  async register(userData: {
    username: string
    email?: string
    password: string
    full_name?: string
  }) {
    const response = await this.client.post('/api/auth/register', userData)
    return response.data
  }

  async getCurrentUser() {
    const response = await this.client.get('/api/auth/me')
    return response.data
  }

  // Portfolio endpoints
  async getPortfolio() {
    const response = await this.client.get('/api/portfolio/')
    return response.data
  }

  async getPortfolioSummary() {
    const response = await this.client.get('/api/portfolio/summary')
    return response.data
  }

  async getGeographicExposure() {
    const response = await this.client.get('/api/portfolio/geographic-exposure')
    return response.data
  }

  // Orders endpoints
  async getOrders(params?: {
    isin?: string
    ticker?: string
    order_type?: string
    status?: string
    date_from?: string
    date_to?: string
    sort_by?: string
    sort_order?: string
    limit?: number
    offset?: number
  }) {
    const response = await this.client.get('/api/orders/', { params })
    return response.data
  }

  async importCSV(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await this.client.post('/api/orders/import-csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  }

  async deleteOrder(orderId: string) {
    const response = await this.client.delete(`/api/orders/${orderId}`)
    return response.data
  }

  async deleteAllOrders() {
    const response = await this.client.delete('/api/orders/all')
    return response.data
  }

  async updateOrder(orderId: string, orderData: any) {
    const response = await this.client.put(`/api/orders/${orderId}`, orderData)
    return response.data
  }

  // Prices endpoints
  async fetchPrices() {
    const response = await this.client.post('/api/prices/fetch')
    return response.data
  }

  async refreshPricesIfNeeded() {
    const response = await this.client.post('/api/prices/refresh-if-needed')
    return response.data
  }

  async getPriceStatus() {
    const response = await this.client.get('/api/prices/status')
    return response.data
  }
}

export const apiClient = new APIClient()
export default apiClient
