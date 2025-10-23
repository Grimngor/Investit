import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')

// Initialize auth on app start
import { useAuthStore } from './stores/auth'
const authStore = useAuthStore()
authStore.initializeAuth()
