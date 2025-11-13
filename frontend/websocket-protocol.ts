/**
 * WebSocket message protocol definitions.
 * This file defines the message types and structures used for WebSocket communication.
 */

export enum WebSocketMessageType {
  // Handshake messages
  HANDSHAKE = "handshake",
  HANDSHAKE_ACK = "handshake.ack",
  
  // Upload progress messages
  FILE_START = "file.start",
  FILE_COMPLETE = "file.complete",
  UPLOAD_PROGRESS = "upload.progress",
  
  // Error messages
  ERROR = "error",
}

export interface HandshakeMessage {
  type: WebSocketMessageType.HANDSHAKE;
  token: string;
}

export interface HandshakeAckMessage {
  type: WebSocketMessageType.HANDSHAKE_ACK;
  user_id: number;
  status: string;
}

export interface ErrorMessage {
  type: WebSocketMessageType.ERROR;
  message: string;
}

export interface FileStartMessage {
  type: "file_start";
  user_id: number;
  current_file: number;
  total_files: number;
  filename: string;
  progress_percent: number;
}

export interface FileCompleteMessage {
  type: "file_complete";
  user_id: number;
  current_file: number;
  total_files: number;
  filename: string;
  progress_percent: number;
  classification?: {
    category: string;
    confidence: number;
  };
  was_cached?: boolean;
}

export type UploadProgressEvent = FileStartMessage | FileCompleteMessage;

export interface UploadProgressMessage {
  type: WebSocketMessageType.UPLOAD_PROGRESS;
  user_id: number;
  current_file: number;
  total_files: number;
  progress_percent: number;
  current_filename: string;
  status: "processing" | "completed" | "error";
}

// Union type for all possible WebSocket messages
export type AnyWebSocketMessage = 
  | HandshakeMessage
  | HandshakeAckMessage
  | ErrorMessage
  | UploadProgressMessage
  | FileStartMessage
  | FileCompleteMessage;
