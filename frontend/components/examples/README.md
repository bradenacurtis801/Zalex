# WebSocket Event System

This directory contains examples of how to use the WebSocket event system.

## Basic Usage

The WebSocket system uses a dispatcher pattern where components register for specific events they care about.

```tsx
import { websocketDispatcher } from '@/contexts/WebSocketContext'
import { WebSocketMessageType } from '@/websocket-protocol'

function MyComponent() {
  useEffect(() => {
    // Register for file start events
    const unsubscribe = websocketDispatcher.register(
      WebSocketMessageType.FILE_START, 
      (data) => {
        console.log('File started:', data.filename)
        // Update UI, show notifications, etc.
      }
    )

    // Cleanup on unmount
    return unsubscribe
  }, [])

  return <div>My Component</div>
}
```

## Available Message Types

- `WebSocketMessageType.FILE_START` - File processing begins
- `WebSocketMessageType.FILE_COMPLETE` - File processing finished
- `WebSocketMessageType.UPLOAD_PROGRESS` - Overall upload progress
- `WebSocketMessageType.ERROR` - Error messages

## Multiple Events

```tsx
useEffect(() => {
  const unsubscribers = [
    websocketDispatcher.register(WebSocketMessageType.FILE_START, handleFileStart),
    websocketDispatcher.register(WebSocketMessageType.FILE_COMPLETE, handleFileComplete),
    websocketDispatcher.register(WebSocketMessageType.ERROR, handleError)
  ]

  return () => {
    unsubscribers.forEach(unsubscribe => unsubscribe())
  }
}, [])
```

## Benefits

- **Explicit**: Clear what events each component listens to
- **Flexible**: Easy to register for any message type
- **Clean**: Automatic cleanup on component unmount
- **Type Safe**: Full TypeScript support
- **Performant**: Only interested components get notified
