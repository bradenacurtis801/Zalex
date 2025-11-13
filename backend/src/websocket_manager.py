"""
WebSocket connection manager for real-time progress updates.
"""

import json
import logging
from typing import Dict
from fastapi import WebSocket, WebSocketDisconnect
from src.event_bus import event_bus, EventType
from fastapi import Depends
from src.websocket_protocol import WebSocketMessageType, WebSocketMessage

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
            # Subscribe to upload progress events
            event_bus.subscribe(EventType.UPLOAD_PROGRESS, self._handle_upload_progress)
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a WebSocket connection and store it."""
        # websocket.accept() is already called in main.py
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected for user: {user_id}")
    
    def disconnect(self, user_id: str):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.debug(f"WebSocket disconnected for user: {user_id}")

    def get_active_connections(self) -> list[str]:
        """Get list of active user IDs."""
        return list(self.active_connections.keys())
    
    def is_connected(self, user_id: str) -> bool:
        """Check if a user has an active WebSocket connection."""
        return user_id in self.active_connections
    
    async def send_progress(self, user_id: str, progress_data: dict):
        """Send progress data to a specific user."""
        if user_id in self.active_connections:
            try:
                # Create proper WebSocket message structure
                message = WebSocketMessage(
                    type=WebSocketMessageType.UPLOAD_PROGRESS,
                    data=progress_data
                )
                await self.active_connections[user_id].send_text(message.model_dump_json())
            except Exception as e:
                logger.error(f"Error sending progress to user {user_id}: {e}")
                self.disconnect(user_id)
        else:
            logger.warning(f"No active connection found for user {user_id}")
    
    async def handle_websocket_connection(self, websocket: WebSocket):
        """Handle the complete WebSocket connection lifecycle including handshake."""
        await websocket.accept()
        
        user_id = None
        try:
            # First, handle the handshake
            user_id = await self._handle_handshake(websocket)
            if not user_id:
                # Authentication failed, connection will be closed
                return
            
            # If handshake successful, start the message loop
            await self._handle_message_loop(websocket, user_id)
            
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user: {user_id}")
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        finally:
            if user_id:
                self.disconnect(str(user_id))

    async def _handle_handshake(self, websocket: WebSocket) -> int:
        """Handle the initial handshake message for authentication."""
        data = await websocket.receive_text()

        message = await self._parse_message(websocket, data)

        if not message or message.get("type") != WebSocketMessageType.HANDSHAKE:
            logger.error(f"Invalid handshake message: {message}")
            await self._send_error(websocket, "Invalid handshake message. Expected: {'type': 'handshake', 'data': {'token': 'your_auth_token'}}")
            return None
        
        token = message.get("data", {}).get("token")
        if not token:
            logger.error("Missing token in handshake data")
            await self._send_error(websocket, "Missing token in handshake data")
            return None

        return await self._authenticate_user(websocket, token)

    async def _handle_message_loop(self, websocket: WebSocket, user_id: int):
        """Handle ongoing messages after successful authentication."""
        while True:
            data = await websocket.receive_text()
            message = await self._parse_message(websocket, data)
            
            if message:
                await self._process_message(websocket, message, user_id)

    async def _process_message(self, websocket: WebSocket, message: dict, user_id: int):
        """Process incoming messages from authenticated user."""
        message_type = message.get("type")

        # For now, we only handle handshake messages
        # Upload progress is handled via event bus, not direct messages
        if message_type not in [WebSocketMessageType.HANDSHAKE]:
            logger.debug(f"Unknown message type from user {user_id}: {message_type}")

    async def _parse_message(self, websocket: WebSocket, data: str) -> dict:
        """Parse JSON message and handle parsing errors."""
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            await self._send_error(websocket, "Invalid JSON message")
            return None

    async def _authenticate_user(self, websocket: WebSocket, token: str) -> int:
        """Authenticate user and complete handshake."""
        from src.db.connection import get_session
        from src.models.database import User
        from src.services.auth_service import AuthService

        # Get database session and auth service
        with next(get_session()) as db:
            auth_service = AuthService(db)

            # Verify session token
            user = auth_service.verify_session_token(token)
            if not user:
                logger.error("Invalid session token")
                await self._send_error(websocket, "Invalid session token")
                return None

            user_id = user.id
            logger.debug(f"User authenticated successfully: {user_id}")

            await self.connect(websocket, str(user_id))

            await self._send_handshake_ack(websocket, user_id)

            logger.debug(f"WebSocket handshake completed for user: {user_id}")
            return user_id

    async def _send_handshake_ack(self, websocket: WebSocket, user_id: int):
        """Send handshake acknowledgment to client."""
        message = WebSocketMessage(
            type=WebSocketMessageType.HANDSHAKE_ACK,
            data={
                "user_id": user_id,
                "status": "connected"
            }
        )
        await websocket.send_text(message.model_dump_json())

    async def _send_error(self, websocket: WebSocket, message: str):
        """Send error message to client."""
        error_msg = WebSocketMessage(
            type=WebSocketMessageType.ERROR,
            data={"message": message}
        )
        await websocket.send_text(error_msg.model_dump_json())


    async def _handle_upload_progress(self, event):
        """Handle upload progress events from the event bus."""
        data = event.data
        user_id = data.get("user_id")

        if not user_id:
            logger.warning("Upload progress event missing user_id")
            return

        # Remove user_id from data before sending to client
        progress_data = {k: v for k, v in data.items() if k != "user_id"}

        await self.send_progress(str(user_id), progress_data)
        logger.debug(f"Handled upload progress event for user {user_id}")


# Singleton instance
connection_manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Dependency injection for ConnectionManager."""
    return connection_manager
