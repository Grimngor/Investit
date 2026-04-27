import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { logger } from './utils/logger'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

// Global error handler
app.config.errorHandler = (err, instance, info) => {
	logger.error('Vue error', {
		error: err instanceof Error ? err.message : String(err),
		info,
		component: instance?.$options.name || 'Unknown',
	})
	console.error('Vue error:', err, info)
}

// Global warning handler (dev only)
if (import.meta.env.DEV) {
	app.config.warnHandler = (msg, instance, trace) => {
		logger.warn('Vue warning', {
			message: msg,
			component: instance?.$options.name || 'Unknown',
			trace,
		})
	}
}

app.use(pinia)

// Initialize auth before installing the router so protected routes can hydrate from localStorage.
const authStore = useAuthStore()
authStore.initializeAuth()

app.use(router)

app.mount('#app')

// Log app startup
logger.info('InvestIt frontend started', {
	env: import.meta.env.MODE,
	version: import.meta.env.VITE_APP_VERSION || 'dev',
})
