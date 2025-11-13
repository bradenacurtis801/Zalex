'use client'

import React, { createContext, useContext, useEffect, useState, useRef, ReactNode } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { createWebSocketUrl } from '@/api'
import { WebSocketMessageType } from '@/websocket-protocol'

interface WebSocketMessage {
  type: string
  data: Record<string, any>
}

interface WebSocketContextType {
  isConnected: boolean
  error: string | null
  register: (messageType: string, handler: (data: Record<string, any>) => void) => () => void
  sendMessage: (message: any) => void
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, logout } = useAuth()
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const ws = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttempts = useRef(0)
  const handlers = useRef<Map<string, Set<(data: Record<string, any>) => void>>>(new Map())

  const register = (messageType: string, handler: (data: Record<string, any>) => void): (() => void) => {
    if (!handlers.current.has(messageType)) {
      handlers.current.set(messageType, new Set())
    }
    
    handlers.current.get(messageType)!.add(handler)
    
    // Return unsubscribe function
    return () => {
      const handlersForType = handlers.current.get(messageType)
      if (handlersForType) {
        handlersForType.delete(handler)
        if (handlersForType.size === 0) {
          handlers.current.delete(messageType)
        }
      }
    }
  }

  const dispatch = (messageType: string, data: Record<string, any>): void => {
    const handlersForType = handlers.current.get(messageType)
    if (handlersForType) {
      handlersForType.forEach(handler => {
        try {
          handler(data)
        } catch (error) {
          console.error(`Error in WebSocket handler for ${messageType}:`, error)
        }
      })
    }
  }

  const connect = () => {
    if (ws.current?.readyState === WebSocket.OPEN || ws.current?.readyState === WebSocket.CONNECTING) {
      return
    }

    // Clean up existing connection
    if (ws.current) {
      ws.current.close()
      ws.current = null
    }
    
    const url = createWebSocketUrl()
    const authToken = typeof window !== 'undefined' ? (localStorage.getItem('auth_token') || '') : ''

    if (!url) {
      console.log('WebSocket disabled - no URL provided')
      return
    }

    try {
      ws.current = new WebSocket(url)
      
      ws.current.onopen = () => {
        // Send handshake message immediately after connection
        sendMessage({
          type: WebSocketMessageType.HANDSHAKE,
          data: {
            token: authToken
          }
        })
      }

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)

          
          if (message.type === WebSocketMessageType.HANDSHAKE_ACK) {
            setIsConnected(true)
            setError(null)
            reconnectAttempts.current = 0 // Reset reconnection attempts on successful connection
          } else if (message.type === WebSocketMessageType.ERROR) {
            const errorMessage = message.data.message || 'WebSocket error'
            console.error('WebSocket error:', errorMessage)
            setError(errorMessage)
            
            // Check if error is related to invalid session token and logout user
            if (errorMessage.toLowerCase().includes('invalid session token') || 
                errorMessage.toLowerCase().includes('session token')) {
              console.warn('Invalid session token detected via WebSocket - logging out user')
              logout()
            }
          } else {
            // Dispatch to all registered handlers
            dispatch(message.type, message.data)
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      ws.current.onerror = (event) => {
        setError('WebSocket connection error')
        
        reconnectAttempts.current++
        const delay = 3000 // Constant 3 second delay
        
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, delay)
      }

      ws.current.onclose = () => {
        setIsConnected(false)
        
        reconnectAttempts.current++
        const delay = 3000 // Constant 3 second delay
        
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, delay)
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

  // Connect when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      connect()
    } else {
      disconnect()
    }
    
    return () => disconnect()
  }, [isAuthenticated])

  const value = {
    isConnected,
    error,
    register,
    sendMessage
  }

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  )
}

export function useWebSocket() {
  const context = useContext(WebSocketContext)
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }
  return context
}

// Export the register function for backward compatibility
export const websocketDispatcher = {
  register: (messageType: string, handler: (data: Record<string, any>) => void) => {
    // This will be set by the provider
    return () => {}
  }
}
