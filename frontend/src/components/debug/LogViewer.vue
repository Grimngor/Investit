<template>
	<div class="log-viewer">
		<div class="log-viewer-header">
			<h3>Frontend Logs</h3>
			<div class="log-viewer-actions">
				<button @click="refresh" class="btn-secondary" title="Refresh logs">
					<span class="icon">🔄</span>
				</button>
				<button @click="downloadLogs" class="btn-secondary" title="Download logs">
					<span class="icon">📥</span>
				</button>
				<button @click="copyLogs" class="btn-secondary" title="Copy to clipboard">
					<span class="icon">📋</span>
				</button>
				<button @click="clearLogs" class="btn-danger" title="Clear all logs">
					<span class="icon">🗑️</span>
				</button>
			</div>
		</div>

		<div class="log-viewer-filters">
			<label>
				<input type="checkbox" v-model="filters.debug" /> DEBUG
			</label>
			<label>
				<input type="checkbox" v-model="filters.info" /> INFO
			</label>
			<label>
				<input type="checkbox" v-model="filters.warn" /> WARN
			</label>
			<label>
				<input type="checkbox" v-model="filters.error" /> ERROR
			</label>
		</div>

		<div class="log-viewer-content" ref="logContainer">
			<div v-if="filteredLogs.length === 0" class="no-logs">No logs available</div>
			<div
				v-for="(log, index) in filteredLogs"
				:key="index"
				:class="['log-entry', `log-${log.level.toLowerCase()}`]"
			>
				<span class="log-timestamp">{{ formatTimestamp(log.timestamp) }}</span>
				<span class="log-level">{{ log.level }}</span>
				<span class="log-message">{{ log.message }}</span>
				<pre v-if="log.context" class="log-context">{{ JSON.stringify(log.context, null, 2) }}</pre>
			</div>
		</div>

		<div v-if="copied" class="copy-notification">Copied to clipboard!</div>
	</div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { logger } from '@/utils/logger'

interface LogEntry {
	timestamp: string
	level: string
	message: string
	context?: Record<string, unknown>
}

const logs = ref<LogEntry[]>([])
const logContainer = ref<HTMLElement>()
const copied = ref(false)

const filters = ref({
	debug: true,
	info: true,
	warn: true,
	error: true,
})

const filteredLogs = computed(() => {
	return logs.value.filter((log) => {
		const level = log.level.toLowerCase()
		return filters.value[level as keyof typeof filters.value]
	})
})

function refresh() {
	logs.value = logger.getLogs()
	scrollToBottom()
}

function formatTimestamp(timestamp: string): string {
	return new Date(timestamp).toLocaleTimeString()
}

function downloadLogs() {
	logger.downloadLogs()
}

async function copyLogs() {
	const content = logger.exportLogs()
	await navigator.clipboard.writeText(content)
	copied.value = true
	setTimeout(() => {
		copied.value = false
	}, 2000)
}

function clearLogs() {
	if (confirm('Are you sure you want to clear all logs?')) {
		logger.clearLogs()
		refresh()
	}
}

function scrollToBottom() {
	if (logContainer.value) {
		setTimeout(() => {
			logContainer.value!.scrollTop = logContainer.value!.scrollHeight
		}, 100)
	}
}

// Auto-refresh logs every 2 seconds
let refreshInterval: number
onMounted(() => {
	refresh()
	refreshInterval = window.setInterval(refresh, 2000)
})

onUnmounted(() => {
	if (refreshInterval) {
		clearInterval(refreshInterval)
	}
})
</script>

<style scoped>
.log-viewer {
	display: flex;
	flex-direction: column;
	height: 100%;
	background: var(--color-background-soft);
	border-radius: 8px;
	overflow: hidden;
}

.log-viewer-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 1rem;
	background: var(--color-background-mute);
	border-bottom: 1px solid var(--color-border);
}

.log-viewer-header h3 {
	margin: 0;
	font-size: 1.125rem;
	font-weight: 600;
}

.log-viewer-actions {
	display: flex;
	gap: 0.5rem;
}

.btn-secondary,
.btn-danger {
	padding: 0.5rem 0.75rem;
	border: none;
	border-radius: 4px;
	cursor: pointer;
	font-size: 0.875rem;
	transition: background-color 0.2s;
}

.btn-secondary {
	background: var(--color-background);
	color: var(--color-text);
}

.btn-secondary:hover {
	background: var(--color-background-soft);
}

.btn-danger {
	background: #dc2626;
	color: white;
}

.btn-danger:hover {
	background: #b91c1c;
}

.icon {
	font-size: 1rem;
}

.log-viewer-filters {
	display: flex;
	gap: 1rem;
	padding: 0.75rem 1rem;
	background: var(--color-background);
	border-bottom: 1px solid var(--color-border);
	font-size: 0.875rem;
}

.log-viewer-filters label {
	display: flex;
	align-items: center;
	gap: 0.25rem;
	cursor: pointer;
}

.log-viewer-content {
	flex: 1;
	overflow-y: auto;
	padding: 1rem;
	font-family: 'Consolas', 'Monaco', monospace;
	font-size: 0.875rem;
	line-height: 1.5;
}

.no-logs {
	text-align: center;
	color: var(--color-text-muted);
	padding: 2rem;
}

.log-entry {
	padding: 0.5rem;
	margin-bottom: 0.25rem;
	border-radius: 4px;
	background: var(--color-background);
}

.log-debug {
	border-left: 3px solid #6b7280;
}

.log-info {
	border-left: 3px solid #3b82f6;
}

.log-warn {
	border-left: 3px solid #f59e0b;
	background: rgba(245, 158, 11, 0.05);
}

.log-error {
	border-left: 3px solid #ef4444;
	background: rgba(239, 68, 68, 0.05);
}

.log-timestamp {
	color: var(--color-text-muted);
	margin-right: 0.5rem;
}

.log-level {
	font-weight: 600;
	margin-right: 0.5rem;
	min-width: 60px;
	display: inline-block;
}

.log-debug .log-level {
	color: #6b7280;
}

.log-info .log-level {
	color: #3b82f6;
}

.log-warn .log-level {
	color: #f59e0b;
}

.log-error .log-level {
	color: #ef4444;
}

.log-message {
	color: var(--color-text);
}

.log-context {
	margin-top: 0.5rem;
	padding: 0.5rem;
	background: var(--color-background-mute);
	border-radius: 4px;
	font-size: 0.8rem;
	overflow-x: auto;
}

.copy-notification {
	position: fixed;
	bottom: 2rem;
	right: 2rem;
	background: #10b981;
	color: white;
	padding: 0.75rem 1.5rem;
	border-radius: 8px;
	box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
	animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
	from {
		transform: translateY(100%);
		opacity: 0;
	}
	to {
		transform: translateY(0);
		opacity: 1;
	}
}
</style>
