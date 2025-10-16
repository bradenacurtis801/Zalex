"""
WebSocket connection manager for real-time progress updates.
"""

import json
import logging
from typing import Dict
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for progress updates."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConnectionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.active_connections: Dict[str, WebSocket] = {}
            self._initialized = True
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a WebSocket connection and store it."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket connected: {client_id}")
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket disconnected: {client_id}")
    
    async def send_progress(self, client_id: str, progress_data: dict):
        """Send progress data to a specific client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(progress_data))
                logger.debug(f"Progress sent to {client_id}: {progress_data}")
            except Exception as e:
                logger.error(f"Error sending progress to {client_id}: {e}")
                self.disconnect(client_id)
        else:
            logger.warning(f"No active connection found for client {client_id}")


# Singleton instance
connection_manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Dependency injection for ConnectionManager."""
    return connection_manager
