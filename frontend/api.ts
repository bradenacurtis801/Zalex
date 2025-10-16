import {
  UploadApi,
  QueryApi,
  CategoryApi,
  FeedbackApi,
  Configuration,
} from "@/generated";

// API configuration utilities
function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL || "";
}

function getApiUrl(): string {
  const apiBaseUrl = getApiBaseUrl();
  
  if (apiBaseUrl) {
    return apiBaseUrl;
  } else {
    // Fallback to current host with development port
    const protocol = window.location.protocol;
    const host = window.location.hostname;
    const port = process.env.NODE_ENV === 'development' ? '5000' : window.location.port;
    return `${protocol}//${host}:${port}`;
  }
}

function getWebSocketUrl(clientId: string): string {
  const apiBaseUrl = getApiBaseUrl();
  
  if (apiBaseUrl) {
    // If API base URL is configured, use it for WebSocket too
    const url = new URL(apiBaseUrl);
    const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${url.host}/ws/${clientId}`;
  } else {
    // Fallback to current host with development port
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    const port = process.env.NODE_ENV === 'development' ? '5000' : window.location.port;
    return `${protocol}//${host}:${port}/ws/${clientId}`;
  }
}

// Use the same base URL logic as WebSocket
let apiBaseUrl = getApiUrl();

// Create a central configuration
let sharedConfig = new Configuration({
  basePath: apiBaseUrl,
});

// Declare API clients (initially with the default sharedConfig)
export let uploadApi = new UploadApi(sharedConfig);
export let queryApi = new QueryApi(sharedConfig);
export let categoryApi = new CategoryApi(sharedConfig);
export let feedbackApi = new FeedbackApi(sharedConfig);

// Function to update the API Base URL dynamically
export const setCurrentClientConfig = (url: string) => {
  apiBaseUrl = url;

  // Update the shared configuration with the new base URL
  sharedConfig = new Configuration({
    basePath: apiBaseUrl,
  });

  // Reinitialize API clients with the updated sharedConfig
  uploadApi = new UploadApi(sharedConfig);
  queryApi = new QueryApi(sharedConfig);
  categoryApi = new CategoryApi(sharedConfig);
  feedbackApi = new FeedbackApi(sharedConfig);
};

// WebSocket utilities
export const createWebSocketUrl = (clientId: string): string => {
  return getWebSocketUrl(clientId);
};

export const generateClientId = (): string => {
  // Try to get existing client ID from localStorage
  const existingClientId = localStorage.getItem('scanpro_client_id');
  if (existingClientId) {
    return existingClientId;
  }
  
  // Generate new client ID and store it
  const newClientId = Math.random().toString(36).substr(2, 9);
  localStorage.setItem('scanpro_client_id', newClientId);
  return newClientId;
};

export const clearClientId = (): void => {
  localStorage.removeItem('scanpro_client_id');
};

// Export the utility functions for consistency
export { getApiUrl, getWebSocketUrl };
