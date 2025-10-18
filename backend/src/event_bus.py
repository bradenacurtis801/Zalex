"""
Event Bus for application-level event handling.
Provides a simple pub/sub pattern for decoupling services.
"""

import asyncio
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
    """
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._async_listeners: Dict[str, List[Callable]] = {}
        self._lock = asyncio.Lock()
    
    def subscribe(self, event_type, callback: Callable) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: The type of event to listen for (str or EventType enum)
            callback: Function to call when event is published
        """
        event_type_str = event_type.value if isinstance(event_type, EventType) else str(event_type)
        if event_type_str not in self._listeners:
            self._listeners[event_type_str] = []
        self._listeners[event_type_str].append(callback)
        logger.debug(f"Subscribed to event type: {event_type_str}")
    
    def subscribe_async(self, event_type, callback: Callable) -> None:
        """
        Subscribe to events of a specific type with async callback.
        
        Args:
            event_type: The type of event to listen for (str or EventType enum)
            callback: Async function to call when event is published
        """
        event_type_str = event_type.value if isinstance(event_type, Enum) else str(event_type)
        if event_type_str not in self._async_listeners:
            self._async_listeners[event_type_str] = []
        self._async_listeners[event_type_str].append(callback)
        logger.debug(f"Subscribed to async event type: {event_type_str}")
    
    def unsubscribe(self, event_type, callback: Callable) -> None:
        """
        Unsubscribe from events of a specific type.
        
        Args:
            event_type: The type of event to stop listening for (str or Enum enum)
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
        
        # Call synchronous listeners
        for callback in self._listeners.get(event_type_str, []):
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event listener for {event_type_str}: {e}")
        
        logger.debug(f"Published event: {event_type_str} from {source}")
    
    async def publish_async(self, event_type, data: Any, source: str = "unknown") -> None:
        """
        Publish an asynchronous event.
        
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
        
        # Call synchronous listeners
        for callback in self._listeners.get(event_type_str, []):
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in sync event listener for {event_type_str}: {e}")
        
        # Call asynchronous listeners
        async with self._lock:
            for callback in self._async_listeners.get(event_type_str, []):
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Error in async event listener for {event_type_str}: {e}")
        
        logger.debug(f"Published async event: {event_type_str} from {source}")
    
    def get_listener_count(self, event_type) -> int:
        """Get the number of listeners for a specific event type."""
        event_type_str = event_type.value if isinstance(event_type, Enum) else str(event_type)
        sync_count = len(self._listeners.get(event_type_str, []))
        async_count = len(self._async_listeners.get(event_type_str, []))
        return sync_count + async_count
    
    def get_all_event_types(self) -> List[str]:
        """Get all event types that have listeners."""
        all_types = set(self._listeners.keys()) | set(self._async_listeners.keys())
        return list(all_types)


# Global event bus instance
event_bus = EventBus()
