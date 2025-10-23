import axios, { type AxiosInstance } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json'
      }
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
      (error) => Promise.reject(error)
    )

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  // Auth endpoints
  async login(username: string, password: string) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const response = await this.client.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    return response.data
  }

  async register(userData: { username: string; email: string; password: string; full_name?: string }) {
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

  async addInvestment(investment: any) {
    const response = await this.client.post('/api/portfolio/', investment)
    return response.data
  }

  async updateInvestment(id: number, investment: any) {
    const response = await this.client.put(`/api/portfolio/${id}`, investment)
    return response.data
  }

  async deleteInvestment(id: number) {
    const response = await this.client.delete(`/api/portfolio/${id}`)
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
}

export const apiClient = new APIClient()
export default apiClient
