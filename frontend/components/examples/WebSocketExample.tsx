/**
 * Example component showing how to use the WebSocket dispatcher directly.
 * This demonstrates the clean, explicit API for registering event handlers.
 */

import React, { useEffect, useState } from 'react'
import { websocketDispatcher } from '@/contexts/WebSocketContext'
import { WebSocketMessageType } from '@/websocket-protocol'

export function WebSocketExample() {
  const [messages, setMessages] = useState<string[]>([])
  const [handlerCount, setHandlerCount] = useState(0)

  // Register for file start events
  useEffect(() => {
    const unsubscribeFileStart = websocketDispatcher.register(
      WebSocketMessageType.FILE_START, 
      (data) => {
        setMessages(prev => [...prev, `File started: ${data.filename}`])
      }
    )

    const unsubscribeFileComplete = websocketDispatcher.register(
      WebSocketMessageType.FILE_COMPLETE, 
      (data) => {
        setMessages(prev => [...prev, `File completed: ${data.filename}`])
      }
    )

    const unsubscribeError = websocketDispatcher.register(
      WebSocketMessageType.ERROR, 
      (data) => {
        console.error('❌ WebSocket error:', data.message)
        setMessages(prev => [...prev, `Error: ${data.message}`])
      }
    )

    // Update handler count (simplified)
    setHandlerCount(1)

    return () => {
      unsubscribeFileStart()
      unsubscribeFileComplete()
      unsubscribeError()
    }
  }, [])

  return (
    <div className="p-4 border rounded-lg">
      <h3 className="text-lg font-semibold mb-2">WebSocket Event Example</h3>
      <p className="text-sm text-gray-600 mb-4">
        This component registers for WebSocket events using the dispatcher directly.
        Check the console and the messages below to see events being received.
      </p>
      
      <div className="mb-4">
        <p className="text-sm">
          <strong>Registered Handlers:</strong> {handlerCount}
        </p>
        <p className="text-sm">
          <strong>Available Types:</strong> FILE_START, FILE_COMPLETE, ERROR
        </p>
      </div>

      <div className="max-h-40 overflow-y-auto">
        <h4 className="font-medium mb-2">Recent Messages:</h4>
        {messages.length === 0 ? (
          <p className="text-gray-500 text-sm">No messages yet...</p>
        ) : (
          <ul className="space-y-1">
            {messages.slice(-10).map((msg, index) => (
              <li key={index} className="text-sm bg-gray-100 p-2 rounded">
                {msg}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

// Example of registering for multiple events at once
export function MultiEventExample() {
  const [events, setEvents] = useState<Record<string, number>>({})

  useEffect(() => {
    const handlers = {
      [WebSocketMessageType.FILE_START]: (data: Record<string, any>) => {
        setEvents(prev => ({ ...prev, 'file.start': (prev['file.start'] || 0) + 1 }))
      },
      [WebSocketMessageType.FILE_COMPLETE]: (data: Record<string, any>) => {
        setEvents(prev => ({ ...prev, 'file.complete': (prev['file.complete'] || 0) + 1 }))
      },
      [WebSocketMessageType.UPLOAD_PROGRESS]: (data: Record<string, any>) => {
        setEvents(prev => ({ ...prev, 'upload.progress': (prev['upload.progress'] || 0) + 1 }))
      }
    }

    // Register all handlers
    const unsubscribers = Object.entries(handlers).map(([messageType, handler]) =>
      websocketDispatcher.register(messageType, handler)
    )

    // Cleanup all on unmount
    return () => {
      unsubscribers.forEach(unsubscribe => unsubscribe())
    }
  }, [])

  return (
    <div className="p-4 border rounded-lg">
      <h3 className="text-lg font-semibold mb-2">Multi-Event Example</h3>
      <p className="text-sm text-gray-600 mb-4">
        This component registers for multiple events at once.
      </p>
      
      <div>
        <h4 className="font-medium mb-2">Event Counts:</h4>
        {Object.entries(events).map(([eventType, count]) => (
          <div key={eventType} className="flex justify-between text-sm">
            <span>{eventType}:</span>
            <span className="font-mono">{count}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
