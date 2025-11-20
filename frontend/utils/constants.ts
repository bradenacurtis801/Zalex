/**
 * Application branding constants
 * 
 * These constants can be overridden via environment variables for easy rebranding.
 * Values are loaded from environment variables with fallback defaults.
 */

/**
 * Can be overridden with NEXT_PUBLIC_APP_NAME environment variable
 */
export const APP_NAME = 'SabioDocs'

/**
 * Full application title displayed in the UI
 * Can be overridden with NEXT_PUBLIC_APP_TITLE environment variable
 */
export const APP_TITLE = process.env.NEXT_PUBLIC_APP_TITLE || `${APP_NAME}`

/**
 * Application description for metadata
 * Can be overridden with NEXT_PUBLIC_APP_DESCRIPTION environment variable
 */
export const APP_DESCRIPTION = 
  process.env.NEXT_PUBLIC_APP_DESCRIPTION || 
  'A self-contained application for document ingestion, OCR, indexing, and retrieval.'


