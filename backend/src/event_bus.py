"""
Event Bus for application-level event handling.
Provides a simple pub/sub pattern for decoupling services.
"""

import asyncio
import inspect
import logging
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    UPLOAD_PROGRESS = "upload.progress"

@dataclass
class Event:
    """Represents an application event."""
    type: str
    data: Any
    timestamp: datetime
    source: str = "unknown"


class EventBus:
    """
    Simple event bus implementation for application-level events.
    Provides pub/sub functionality for decoupling services.
    Auto-detects async vs sync callbacks and handles them appropriately.
    """
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._lock = asyncio.Lock()
    
    def subscribe(self, event_type, callback: Callable) -> None:
        """
        Subscribe to events of a specific type.
        Works with both sync and async callbacks - auto-detected.
        
        Args:
            event_type: The type of event to listen for (str or EventType enum)
            callback: Function (sync or async) to call when event is published
        """
        event_type_str = event_type.value if isinstance(event_type, EventType) else str(event_type)
        if event_type_str not in self._listeners:
            self._listeners[event_type_str] = []
        self._listeners[event_type_str].append(callback)
        callback_type = "async" if inspect.iscoroutinefunction(callback) else "sync"
        logger.debug(f"Subscribed {callback_type} callback to event type: {event_type_str}")
    
    def unsubscribe(self, event_type, callback: Callable) -> None:
        """
        Unsubscribe from events of a specific type.
        
        Args:
            event_type: The type of event to stop listening for (str or Enum)
            callback: Function to remove from listeners
        """
        event_type_str = event_type.value if isinstance(event_type, Enum) else str(event_type)
        if event_type_str in self._listeners:
            try:
                self._listeners[event_type_str].remove(callback)
                logger.debug(f"Unsubscribed from event type: {event_type_str}")
            except ValueError:
                logger.warning(f"Callback not found for event type: {event_type_str}")
    
    def publish(self, event_type, data: Any, source: str = "unknown") -> None:
        """
        Publish a synchronous event.
        Sync callbacks are called directly, async callbacks are scheduled if event loop is running.
        
        Args:
            event_type: The type of event being published (str or EventType enum)
            data: Event data to pass to listeners
            source: Source of the event for debugging
        """
        event_type_str = event_type.value if isinstance(event_type, Enum) else str(event_type)
        event = Event(
            type=event_type_str,
            data=data,
            timestamp=datetime.now(),
            source=source
        )
        
        # Process all listeners
        for callback in self._listeners.get(event_type_str, []):
            try:
                if inspect.iscoroutinefunction(callback):
                    # Async callback in sync context - try to schedule it
                    try:
                        loop = asyncio.get_running_loop()
                        # Event loop is running - schedule the coroutine
                        loop.create_task(callback(event))
                    except RuntimeError:
                        # No event loop running - can't execute async callback from sync context
                        logger.warning(
                            f"Async callback for {event_type_str} cannot be executed from sync context. "
                            f"Use publish_async() instead or ensure event loop is running."
                        )
                else:
                    # Sync callback - call directly
                    callback(event)
            except Exception as e:
                logger.error(f"Error in event listener for {event_type_str}: {e}")
        
        logger.debug(f"Published event: {event_type_str} from {source}")
    
    async def publish_async(self, event_type, data: Any, source: str = "unknown") -> None:
        """
        Publish an asynchronous event.
        Both sync and async callbacks are handled appropriately.
        
        Args:
            event_type: The type of event being published (str or EventType enum)
            data: Event data to pass to listeners
            source: Source of the event for debugging
        """
        event_type_str = event_type.value if isinstance(event_type, Enum) else str(event_type)
        event = Event(
            type=event_type_str,
            data=data,
            timestamp=datetime.now(),
            source=source
        )
        
        # Process all listeners
        async with self._lock:
            for callback in self._listeners.get(event_type_str, []):
                try:
                    if inspect.iscoroutinefunction(callback):
                        # Async callback - await it
                        await callback(event)
                    else:
                        # Sync callback - call directly (can be called from async context)
                        callback(event)
                except Exception as e:
                    logger.error(f"Error in event listener for {event_type_str}: {e}")
        
        logger.debug(f"Published async event: {event_type_str} from {source}")
    
    def get_listener_count(self, event_type) -> int:
        """Get the number of listeners for a specific event type."""
        event_type_str = event_type.value if isinstance(event_type, Enum) else str(event_type)
        return len(self._listeners.get(event_type_str, []))
    
    def get_all_event_types(self) -> List[str]:
        """Get all event types that have listeners."""
        return list(self._listeners.keys())


# Global event bus instance
event_bus = EventBus()
