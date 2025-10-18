"""
WebSocket message protocol definitions.
This file defines the message types and structures used for WebSocket communication.
"""

from enum import Enum
from typing import Dict, Any
from pydantic import BaseModel


class WebSocketMessageType(str, Enum):
    """WebSocket message types."""
    # Handshake messages
    HANDSHAKE = "handshake"
    HANDSHAKE_ACK = "handshake.ack"
    
    # Upload progress messages
    FILE_START = "file.start"
    FILE_COMPLETE = "file.complete"
    UPLOAD_PROGRESS = "upload.progress"
    
    # Error messages
    ERROR = "error"


class WebSocketMessage(BaseModel):
    """Generic WebSocket message structure."""
    type: WebSocketMessageType
    data: Dict[str, Any]
