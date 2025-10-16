'use client'

import { useEffect, useRef, useState } from 'react'

interface WebSocketMessage {
  type: 'file_start' | 'file_complete' | 'error'
  current_file: number
  total_files: number
  filename: string
  progress_percent: number
  classification?: {
    category: string
    confidence: number
  }
  error?: string
}

interface UseWebSocketProps {
  url: string
  onMessage?: (message: WebSocketMessage) => void
  onError?: (error: Event) => void
  onOpen?: () => void
  onClose?: () => void
}

export function useWebSocket({
  url,
  onMessage,
  onError,
  onOpen,
  onClose
}: UseWebSocketProps) {
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const ws = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5

  const connect = () => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      ws.current = new WebSocket(url)
      
      ws.current.onopen = () => {
        setIsConnected(true)
        setError(null)
        console.log('WebSocket connected')
        reconnectAttempts.current = 0
        onOpen?.()
      }

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          onMessage?.(message)
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      ws.current.onerror = (event) => {
        setError('WebSocket connection error')
        onError?.(event)
        
        // Also attempt to reconnect on error
        console.log('WebSocket error, attempting to reconnect...')
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++
          console.log(`Reconnection attempt ${reconnectAttempts.current}/${maxReconnectAttempts}`)
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, 1000) // Fixed 1 second delay
        } else {
          console.log('Max reconnection attempts reached, stopping reconnection')
        }
      }

      ws.current.onclose = () => {
        setIsConnected(false)
        onClose?.()

        console.log('WebSocket disconnected, reconnecting...')
        // Attempt to reconnect
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++
          console.log(`Reconnection attempt ${reconnectAttempts.current}/${maxReconnectAttempts}`)
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, 1000) // Fixed 1 second delay
        } else {
          console.log('Max reconnection attempts reached, stopping reconnection')
        }
      }
    } catch (err) {
      setError('Failed to create WebSocket connection')
      console.error('WebSocket connection error:', err)
    }
  }

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (ws.current) {
      ws.current.close()
      ws.current = null
    }
    setIsConnected(false)
  }

  const sendMessage = (message: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message))
    }
  }

  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [])

  return {
    isConnected,
    error,
    connect,
    disconnect,
    sendMessage
  }
}
