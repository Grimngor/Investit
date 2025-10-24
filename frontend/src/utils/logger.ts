/**
 * Frontend logging utility with persistent storage
 */

export enum LogLevel {
	DEBUG = 0,
	INFO = 1,
	WARN = 2,
	ERROR = 3,
}

interface LogEntry {
	timestamp: string
	level: string
	message: string
	context?: Record<string, unknown>
}

class Logger {
	private level: LogLevel
	private maxLogs: number = 1000
	private storageKey: string = 'investit_logs'

	constructor(level: LogLevel = LogLevel.INFO) {
		this.level = import.meta.env.DEV ? LogLevel.DEBUG : level
	}

	private formatMessage(level: string, message: string, context?: Record<string, unknown>): string {
		const timestamp = new Date().toISOString()
		const contextStr = context ? ` | ${JSON.stringify(context)}` : ''
		return `[${timestamp}] [${level}] ${message}${contextStr}`
	}

	private persistLog(level: string, message: string, context?: Record<string, unknown>): void {
		try {
			const logs = this.getLogs()
			const entry: LogEntry = {
				timestamp: new Date().toISOString(),
				level,
				message,
				...(context && { context }),
			}

			logs.push(entry)

			// Keep only the most recent logs
			if (logs.length > this.maxLogs) {
				logs.splice(0, logs.length - this.maxLogs)
			}

			localStorage.setItem(this.storageKey, JSON.stringify(logs))
		} catch (error) {
			// If localStorage is full or unavailable, fail silently
			console.warn('Failed to persist log:', error)
		}
	}

	debug(message: string, context?: Record<string, unknown>): void {
		if (this.level <= LogLevel.DEBUG) {
			console.debug(this.formatMessage('DEBUG', message, context))
			this.persistLog('DEBUG', message, context)
		}
	}

	info(message: string, context?: Record<string, unknown>): void {
		if (this.level <= LogLevel.INFO) {
			console.info(this.formatMessage('INFO', message, context))
			this.persistLog('INFO', message, context)
		}
	}

	warn(message: string, context?: Record<string, unknown>): void {
		if (this.level <= LogLevel.WARN) {
			console.warn(this.formatMessage('WARN', message, context))
			this.persistLog('WARN', message, context)
		}
	}

	error(message: string, context?: Record<string, unknown>): void {
		if (this.level <= LogLevel.ERROR) {
			console.error(this.formatMessage('ERROR', message, context))
			this.persistLog('ERROR', message, context)
		}
	}

	/**
	 * Get all persisted logs from localStorage
	 */
	getLogs(): LogEntry[] {
		try {
			const logs = localStorage.getItem(this.storageKey)
			return logs ? JSON.parse(logs) : []
		} catch {
			return []
		}
	}

	/**
	 * Export logs as text for easy copying
	 */
	exportLogs(): string {
		const logs = this.getLogs()
		return logs.map((log) => this.formatMessage(log.level, log.message, log.context)).join('\n')
	}

	/**
	 * Clear all persisted logs
	 */
	clearLogs(): void {
		localStorage.removeItem(this.storageKey)
	}

	/**
	 * Download logs as a file
	 */
	downloadLogs(filename: string = 'investit-frontend-logs.txt'): void {
		const content = this.exportLogs()
		const blob = new Blob([content], { type: 'text/plain' })
		const url = URL.createObjectURL(blob)
		const link = document.createElement('a')
		link.href = url
		link.download = filename
		link.click()
		URL.revokeObjectURL(url)
	}
}

// Export singleton instance
export const logger = new Logger()

// Export default for convenience
export default logger
