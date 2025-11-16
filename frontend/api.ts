import {
  UploadApi,
  QueryApi,
  CategoryApi,
  FeedbackApi,
  AuthApi,
  OcrApi,
  TasksApi,
  Configuration,
  Middleware,
  ResponseContext,
} from "@/generated";

// Use relative URLs to leverage Next.js proxy
let apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || '';

// Keep an in-memory token so we can immediately use fresh tokens after login
let currentToken: string | null = null;

// Global logout callback that will be set by AuthContext
let globalLogoutCallback: (() => void) | null = null;

// Function to set the logout callback from AuthContext
export const setLogoutCallback = (callback: (() => void) | null) => {
  globalLogoutCallback = callback;
};

// Middleware to handle 401 responses and automatically log out
const authErrorMiddleware: Middleware = {
  post: async (context: ResponseContext): Promise<Response | void> => {
    // Check if response is 401 Unauthorized
    // Exclude login endpoint - 401 there means wrong credentials, not expired token
    if (context.response.status === 401 && !context.url.includes('/api/auth/login')) {
      // Call the global logout callback if it's set
      if (globalLogoutCallback) {
        globalLogoutCallback();
      }
    }
    return context.response;
  },
};

// Callback function to get the current token
const getCurrentToken = async (): Promise<string> => {
  const token = typeof window !== 'undefined'
    ? (currentToken ?? localStorage.getItem('auth_token'))
    : currentToken;
  return token || '';
};

// Create initial configuration with auth error middleware
let sharedConfig = new Configuration({
  basePath: apiBaseUrl,
  accessToken: getCurrentToken,
  middleware: [authErrorMiddleware],
});

// Declare API clients (initially with the default sharedConfig)
export let uploadApi = new UploadApi(sharedConfig);
export let queryApi = new QueryApi(sharedConfig);
export let categoryApi = new CategoryApi(sharedConfig);
export let feedbackApi = new FeedbackApi(sharedConfig);
export let authApi = new AuthApi(sharedConfig);
export let ocrApi = new OcrApi(sharedConfig);
export let taskApi = new TasksApi(sharedConfig);

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
    middleware: [authErrorMiddleware],
  });

  // Reinitialize API clients with the updated sharedConfig
  uploadApi = new UploadApi(sharedConfig);
  queryApi = new QueryApi(sharedConfig);
  categoryApi = new CategoryApi(sharedConfig);
  feedbackApi = new FeedbackApi(sharedConfig);
  authApi = new AuthApi(sharedConfig);
  ocrApi = new OcrApi(sharedConfig);
  taskApi = new TasksApi(sharedConfig);
};

// WebSocket utilities
export const createWebSocketUrl = (): string => {
  // WebSocket connects through custom Next.js server proxy
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws`;
};

