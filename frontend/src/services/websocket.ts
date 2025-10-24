import { logger } from '@/utils/logger'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'

type MessageHandler = (data: any) => void

class WebSocketClient {
  private ws: WebSocket | null = null
  private handlers: Map<string, MessageHandler[]> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectInterval = 3000

  connect(token?: string) {
    // Connection guard - prevent duplicate connections
    if (this.ws?.readyState === WebSocket.OPEN || this.ws?.readyState === WebSocket.CONNECTING) {
      logger.debug('WebSocket already connected or connecting, skipping')
      return
    }

    const url = token ? `${WS_URL}?token=${token}` : WS_URL

    try {
      this.ws = new WebSocket(url)

      this.ws.onopen = () => {
        logger.info('WebSocket connection opened')
        this.reconnectAttempts = 0

        // Send ping on connect
        this.send({ type: 'ping' })
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          // Handle handshake
          if (data.type === 'connection_status') {
            logger.debug('WebSocket handshake received', { data })
            return
          }

          // Handle pong
          if (data.type === 'pong') {
            logger.debug('WebSocket pong received')
            return
          }

          // Dispatch to handlers
          const handlers = this.handlers.get(data.type) || []
          handlers.forEach(handler => handler(data))
        } catch (error) {
          logger.error('WebSocket error parsing message', { error })
        }
      }

      this.ws.onerror = (error) => {
        logger.error('WebSocket error', { error })
      }

      this.ws.onclose = (event) => {
        logger.info('WebSocket connection closed', { code: event.code, reason: event.reason })

        // Don't reconnect on code 1008 (policy violation - auth failed)
        if (event.code === 1008) {
          logger.warn('WebSocket auth failed, not reconnecting')
          return
        }

        // Attempt to reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++
          logger.info('WebSocket reconnecting', { attempt: this.reconnectAttempts, max: this.maxReconnectAttempts })

          setTimeout(() => {
            this.connect(token)
          }, this.reconnectInterval * this.reconnectAttempts)
        } else {
          logger.warn('WebSocket max reconnect attempts reached')
        }
      }
    } catch (error) {
      logger.error('WebSocket connection error', { error })
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      logger.warn('WebSocket cannot send message, connection not open')
    }
  }

  on(type: string, handler: MessageHandler) {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, [])
    }
    this.handlers.get(type)!.push(handler)
  }

  off(type: string, handler: MessageHandler) {
    const handlers = this.handlers.get(type)
    if (handlers) {
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    }
  }
}

export const wsClient = new WebSocketClient()
export default wsClient
