import axios, { AxiosError, AxiosInstance, AxiosResponse } from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const API_TIMEOUT_MS = 30000;

const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: API_TIMEOUT_MS,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use(
  (config) => {
    if (import.meta.env.DEV) {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    if (error.response) {
      const status = error.response.status;
      const message =
        (error.response.data as { detail?: string })?.detail ||
        "An error occurred";

      console.error(`[API Error] ${status}: ${message}`);

      if (status === 401) {
        console.error("Unauthorized access");
      } else if (status === 503) {
        console.error("Service temporarily unavailable");
      }
    } else if (error.request) {
      console.error("[API Error] No response received from server");
    } else {
      console.error("[API Error]", error.message);
    }

    return Promise.reject(error);
  }
);

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
}

export const api = {
  health: async (): Promise<HealthResponse> => {
    const response = await apiClient.get<HealthResponse>("/health");
    return response.data;
  },

  get: async <T>(url: string): Promise<T> => {
    const response = await apiClient.get<T>(url);
    return response.data;
  },

  post: async <T, D = unknown>(url: string, data?: D): Promise<T> => {
    const response = await apiClient.post<T>(url, data);
    return response.data;
  },

  patch: async <T, D = unknown>(url: string, data?: D): Promise<T> => {
    const response = await apiClient.patch<T>(url, data);
    return response.data;
  },

  delete: async <T>(url: string): Promise<T> => {
    const response = await apiClient.delete<T>(url);
    return response.data;
  },
};

export default apiClient;
