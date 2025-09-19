import {
  UploadApi,
  QueryApi,
  Configuration,
} from "@/generated";

let apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

// Create a central configuration
let sharedConfig = new Configuration({
  basePath: apiBaseUrl,
});

// Declare API clients (initially with the default sharedConfig)
export let uploadApi = new UploadApi(sharedConfig);
export let queryApi = new QueryApi(sharedConfig);

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
};
