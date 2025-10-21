import {
  UploadApi,
  QueryApi,
  CategoryApi,
  FeedbackApi,
  AuthApi,
  OcrApi,
  Configuration,
} from "@/generated";

// Use relative URLs to leverage Next.js proxy
let apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || '';

// Keep an in-memory token so we can immediately use fresh tokens after login
let currentToken: string | null = null;

// Callback function to get the current token
const getCurrentToken = async (): Promise<string> => {
  const token = typeof window !== 'undefined'
    ? (currentToken ?? localStorage.getItem('auth_token'))
    : currentToken;
  return token || '';
};

// Create initial configuration
let sharedConfig = new Configuration({
  basePath: apiBaseUrl,
  accessToken: getCurrentToken,
});

// Declare API clients (initially with the default sharedConfig)
export let uploadApi = new UploadApi(sharedConfig);
export let queryApi = new QueryApi(sharedConfig);
export let categoryApi = new CategoryApi(sharedConfig);
export let feedbackApi = new FeedbackApi(sharedConfig);
export let authApi = new AuthApi(sharedConfig);
export let ocrApi = new OcrApi(sharedConfig);

// Function to update the API Base URL dynamically
export const setCurrentClientConfig = (url: string) => {
  apiBaseUrl = url;
  updateApiClients();
};

// Allow setting/clearing the auth token explicitly (e.g., after login/logout)
export const setAuthToken = (token: string | null) => {
  currentToken = token;
  if (typeof window !== 'undefined') {
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }
  updateApiClients();
};

// Function to update API clients with current authentication
export const updateApiClients = () => {
  sharedConfig = new Configuration({
    basePath: apiBaseUrl,
    accessToken: getCurrentToken,
  });

  // Reinitialize API clients with the updated sharedConfig
  uploadApi = new UploadApi(sharedConfig);
  queryApi = new QueryApi(sharedConfig);
  categoryApi = new CategoryApi(sharedConfig);
  feedbackApi = new FeedbackApi(sharedConfig);
  authApi = new AuthApi(sharedConfig);
  ocrApi = new OcrApi(sharedConfig);
};

// WebSocket utilities
export const createWebSocketUrl = (): string => {
  // WebSocket connects through custom Next.js server proxy
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws`;
};

