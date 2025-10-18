/**
 * Browser cache utilities for managing HTTP cache.
 * This is a simple utility to work with the browser's built-in HTTP caching.
 */

import { uploadApi } from '@/api'

/**
 * Clear browser cache for PDF pages by making a request with cache-busting headers.
 * This forces the browser to fetch fresh data from the server.
 */
export async function clearPdfCache(documentId: string): Promise<void> {
  try {
    // Use the API with cache-busting headers
    await uploadApi.getPdfPagesApiDocumentsDocumentIdPagesGet({
      documentId: documentId
    }, {
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    });
    
;
  } catch (error) {
    console.error('Error clearing PDF cache:', error);
    throw error;
  }
}

/**
 * Check if the browser has cached data for a PDF by making a conditional request.
 * This uses the ETag header to check if the cached version is still valid.
 */
export async function isPdfCached(documentId: string): Promise<boolean> {
  try {
    // Use the API with conditional request headers
    const response = await uploadApi.getPdfPagesApiDocumentsDocumentIdPagesGetRaw({
      documentId: documentId
    }, {
      method: 'HEAD',
      headers: {
        'If-None-Match': `"${documentId}"`
      }
    });
    
    // 304 Not Modified means the cached version is still valid
    return response.raw.status === 304;
  } catch (error) {
    console.error('Error checking PDF cache:', error);
    return false;
  }
}

/**
 * Preload PDF pages into browser cache.
 * This can be called when the user hovers over a PDF document to warm the cache.
 */
export async function preloadPdfPages(documentId: string): Promise<void> {
  try {
    await uploadApi.getPdfPagesApiDocumentsDocumentIdPagesGet({
      documentId: documentId
    });
    
;
  } catch (error) {
    console.error('Error preloading PDF pages:', error);
    // Don't throw - preloading is optional
  }
}
