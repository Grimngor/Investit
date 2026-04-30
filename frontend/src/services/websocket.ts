import { logger } from '@/utils/logger'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'

type MessageHandler = (data: any) => void

class WebSocketClient {
  private ws: WebSocket | null = null
  private handlers: Map<string, MessageHandler[]> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectInterval = 3000
  private authToken: string | null = null
  private shouldReconnect = false

  connect(token?: string) {
    if (token) {
      this.authToken = token
    }
    this.shouldReconnect = true

    // Connection guard - prevent duplicate connections
    if (this.ws?.readyState === WebSocket.OPEN || this.ws?.readyState === WebSocket.CONNECTING) {
      logger.debug('WebSocket already connected or connecting, skipping')
      return
    }

    try {
      this.ws = new WebSocket(WS_URL)

      this.ws.onopen = () => {
        logger.info('WebSocket connection opened')
        this.reconnectAttempts = 0

        if (this.authToken) {
          this.send({ type: 'auth', token: this.authToken })
        } else {
          logger.warn('WebSocket opened without an auth token')
        }
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          // Handle handshake
          if (data.type === 'connection_status') {
            logger.debug('WebSocket handshake received', { data })
            this.send({ type: 'ping' })
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

        if (!this.shouldReconnect) {
          return
        }

        // Don't reconnect on code 1008 (policy violation - auth failed)
        if (event.code === 1008) {
          logger.warn('WebSocket auth failed, not reconnecting')
          this.shouldReconnect = false
          return
        }

        // Attempt to reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++
          logger.info('WebSocket reconnecting', { attempt: this.reconnectAttempts, max: this.maxReconnectAttempts })

          setTimeout(() => {
            if (this.shouldReconnect) {
              this.connect(this.authToken || undefined)
            }
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
    this.shouldReconnect = false
    this.authToken = null

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
