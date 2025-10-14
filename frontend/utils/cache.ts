/**
 * Browser cache utilities for managing HTTP cache.
 * This is a simple utility to work with the browser's built-in HTTP caching.
 */

/**
 * Clear browser cache for PDF pages by making a request with cache-busting headers.
 * This forces the browser to fetch fresh data from the server.
 */
export async function clearPdfCache(filename: string): Promise<void> {
  try {
    // Make a request with cache-busting headers
    const response = await fetch(`/api/documents/${encodeURIComponent(filename)}/pages`, {
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Failed to clear cache: ${response.status}`);
    }
    
    console.log(`Cache cleared for PDF: ${filename}`);
  } catch (error) {
    console.error('Error clearing PDF cache:', error);
    throw error;
  }
}

/**
 * Check if the browser has cached data for a PDF by making a conditional request.
 * This uses the ETag header to check if the cached version is still valid.
 */
export async function isPdfCached(filename: string): Promise<boolean> {
  try {
    // Make a conditional request with If-None-Match header
    const response = await fetch(`/api/documents/${encodeURIComponent(filename)}/pages`, {
      method: 'HEAD',
      headers: {
        'If-None-Match': `"${filename}"`
      }
    });
    
    // 304 Not Modified means the cached version is still valid
    return response.status === 304;
  } catch (error) {
    console.error('Error checking PDF cache:', error);
    return false;
  }
}

/**
 * Preload PDF pages into browser cache.
 * This can be called when the user hovers over a PDF document to warm the cache.
 */
export async function preloadPdfPages(filename: string): Promise<void> {
  try {
    const response = await fetch(`/api/documents/${encodeURIComponent(filename)}/pages`);
    
    if (!response.ok) {
      throw new Error(`Failed to preload PDF: ${response.status}`);
    }
    
    console.log(`PDF pages preloaded: ${filename}`);
  } catch (error) {
    console.error('Error preloading PDF pages:', error);
    // Don't throw - preloading is optional
  }
}
