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
      console.log('[WebSocket] Already connected or connecting, skipping...')
      return
    }

    const url = token ? `${WS_URL}?token=${token}` : WS_URL
    
    try {
      this.ws = new WebSocket(url)

      this.ws.onopen = () => {
        console.log('[WebSocket] Connection opened')
        this.reconnectAttempts = 0
        
        // Send ping on connect
        this.send({ type: 'ping' })
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          // Handle handshake
          if (data.type === 'connection_status') {
            console.log('[WebSocket] Handshake received:', data)
            return
          }
          
          // Handle pong
          if (data.type === 'pong') {
            console.log('[WebSocket] Pong received')
            return
          }
          
          // Dispatch to handlers
          const handlers = this.handlers.get(data.type) || []
          handlers.forEach(handler => handler(data))
        } catch (error) {
          console.error('[WebSocket] Error parsing message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error)
      }

      this.ws.onclose = (event) => {
        console.log(`[WebSocket] Connection closed. Code: ${event.code}, Reason: ${event.reason}`)
        
        // Don't reconnect on code 1008 (policy violation - auth failed)
        if (event.code === 1008) {
          console.log('[WebSocket] Auth failed, not reconnecting')
          return
        }
        
        // Attempt to reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++
          console.log(`[WebSocket] Reconnecting... Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`)
          
          setTimeout(() => {
            this.connect(token)
          }, this.reconnectInterval * this.reconnectAttempts)
        } else {
          console.log('[WebSocket] Max reconnect attempts reached')
        }
      }
    } catch (error) {
      console.error('[WebSocket] Connection error:', error)
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
      console.warn('[WebSocket] Cannot send message, connection not open')
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
