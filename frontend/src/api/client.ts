/**
 * API 클라이언트 모듈
 *
 * Axios 기반 HTTP 클라이언트로 백엔드 API와 통신합니다.
 * - 기본 URL 및 타임아웃 설정
 * - 요청/응답 인터셉터 (로깅, 오류 처리)
 * - 공통 API 메서드 제공
 */

import axios, { AxiosError, AxiosInstance, AxiosResponse } from "axios";

// === API 설정 상수 ===
const DEFAULT_API_URL = "http://localhost:8000";
const API_BASE_URL = import.meta.env.VITE_API_URL ?? DEFAULT_API_URL;
const API_TIMEOUT_MS = 30000; // 요청 타임아웃 (30초)

// === Auth 설정 상수 ===
const AUTH_STORAGE_KEY = "auth";
const DEFAULT_AUTH_API_URL = "http://localhost:9000";
const AUTH_API_URL =
  import.meta.env.VITE_AUTH_API_URL ?? DEFAULT_AUTH_API_URL;

// === HTTP 상태 코드 상수 ===
const HTTP_STATUS = {
  UNAUTHORIZED: 401,
  SERVICE_UNAVAILABLE: 503,
} as const;

// === 로깅 상수 ===
const LOG_PREFIX = {
  API: "[API]",
  ERROR: "[API 오류]",
} as const;

/**
 * API 오류 응답 인터페이스
 */
interface ErrorResponse {
  detail?: string;
}

/**
 * 저장된 인증 정보 인터페이스
 */
interface StoredAuth {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

/**
 * 토큰 갱신 응답 인터페이스
 */
interface RefreshResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

/**
 * localStorage에서 인증 정보 로드
 */
function getStoredAuth(): StoredAuth | null {
  try {
    const stored = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!stored) return null;
    return JSON.parse(stored) as StoredAuth;
  } catch {
    return null;
  }
}

/**
 * localStorage에 인증 정보 저장
 */
function saveStoredAuth(auth: StoredAuth): void {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(auth));
}

/**
 * localStorage의 인증 정보 삭제 및 로그인 페이지로 리다이렉트
 */
function clearAuthAndRedirect(): void {
  localStorage.removeItem(AUTH_STORAGE_KEY);
  // 현재 페이지가 로그인 페이지가 아닌 경우에만 리다이렉트
  if (window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
}

// 토큰 갱신 중복 요청 방지를 위한 상태
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

/**
 * 토큰 갱신 대기열에 추가
 */
function subscribeTokenRefresh(callback: (token: string) => void): void {
  refreshSubscribers.push(callback);
}

/**
 * 토큰 갱신 완료 후 대기 중인 요청들 처리
 */
function onRefreshed(token: string): void {
  refreshSubscribers.forEach((callback) => callback(token));
  refreshSubscribers = [];
}

/**
 * Axios 인스턴스 생성
 *
 * 백엔드 API와 통신을 위한 설정된 클라이언트입니다.
 * - baseURL: /api/v1 접두사 포함
 * - timeout: 30초
 * - Content-Type: application/json
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: API_TIMEOUT_MS,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * 요청 인터셉터
 *
 * 모든 요청 전에 실행됩니다.
 * - Authorization 헤더에 액세스 토큰 추가
 * - 개발 모드에서 요청 로그 출력
 */
apiClient.interceptors.request.use(
  (config) => {
    // localStorage에서 인증 정보 로드하여 Authorization 헤더 추가
    const auth = getStoredAuth();
    if (auth?.accessToken) {
      config.headers.Authorization = `Bearer ${auth.accessToken}`;
    }

    // 개발 모드에서만 요청 로깅
    if (import.meta.env.DEV) {
      console.log(
        `${LOG_PREFIX.API} ${config.method?.toUpperCase()} ${config.url}`
      );
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * 응답 인터셉터
 *
 * 모든 응답에 대해 실행됩니다.
 * - 성공: 응답 그대로 반환
 * - 401 오류: 토큰 갱신 시도 후 재요청
 * - 기타 오류: 상태 코드별 오류 처리 및 로깅
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error: AxiosError<ErrorResponse>) => {
    const originalRequest = error.config;

    if (error.response) {
      const status = error.response.status;
      const message = error.response.data?.detail || "오류가 발생했습니다";

      // 401 Unauthorized - 토큰 갱신 시도
      if (status === HTTP_STATUS.UNAUTHORIZED && originalRequest) {
        const auth = getStoredAuth();

        // 리프레시 토큰이 없으면 로그인 페이지로
        if (!auth?.refreshToken) {
          clearAuthAndRedirect();
          return Promise.reject(error);
        }

        // 이미 토큰 갱신 중이면 대기열에 추가
        if (isRefreshing) {
          return new Promise((resolve) => {
            subscribeTokenRefresh((token: string) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              resolve(apiClient(originalRequest));
            });
          });
        }

        // 토큰 갱신 시작
        isRefreshing = true;

        try {
          // Auth Server에 토큰 갱신 요청
          const response = await axios.post<RefreshResponse>(
            `${AUTH_API_URL}/api/v1/auth/refresh`,
            { refresh_token: auth.refreshToken },
            { headers: { "Content-Type": "application/json" } }
          );

          const newAccessToken = response.data.access_token;
          const newExpiresAt = Date.now() + response.data.expires_in * 1000;

          // localStorage 업데이트
          saveStoredAuth({
            ...auth,
            accessToken: newAccessToken,
            expiresAt: newExpiresAt,
          });

          if (import.meta.env.DEV) {
            console.log("[API] 토큰 갱신 성공");
          }

          // 대기 중인 요청들 처리
          onRefreshed(newAccessToken);
          isRefreshing = false;

          // 원래 요청 재시도
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return apiClient(originalRequest);
        } catch (refreshError) {
          // 토큰 갱신 실패 - 로그인 페이지로
          isRefreshing = false;
          refreshSubscribers = [];
          console.error("[API] 토큰 갱신 실패, 로그아웃");
          clearAuthAndRedirect();
          return Promise.reject(refreshError);
        }
      }

      console.error(`${LOG_PREFIX.ERROR} ${status}: ${message}`);

      // 503 서비스 불가
      if (status === HTTP_STATUS.SERVICE_UNAVAILABLE) {
        console.error("서비스 일시 중단");
      }
    } else if (error.request) {
      // 요청은 보냈으나 응답이 없는 경우
      console.error(`${LOG_PREFIX.ERROR} 서버로부터 응답 없음`);
    } else {
      // 요청 설정 중 오류 발생
      console.error(LOG_PREFIX.ERROR, error.message);
    }

    return Promise.reject(error);
  }
);

/**
 * 헬스체크 응답 타입
 */
export interface HealthResponse {
  status: string; // 서버 상태 (healthy/unhealthy)
  timestamp: string; // 응답 시간
  version: string; // API 버전
}

/**
 * API 메서드 모음
 *
 * 백엔드 API와 통신하기 위한 공통 메서드를 제공합니다.
 */
export const api = {
  /**
   * 헬스체크 API 호출
   *
   * @returns Promise<HealthResponse> 서버 상태 정보
   */
  health: async (): Promise<HealthResponse> => {
    const response = await apiClient.get<HealthResponse>("/health");
    return response.data;
  },

  /**
   * GET 요청
   *
   * @template T 응답 데이터 타입
   * @param url API 엔드포인트
   * @returns Promise<T> 응답 데이터
   */
  get: async <T>(url: string): Promise<T> => {
    const response = await apiClient.get<T>(url);
    return response.data;
  },

  /**
   * POST 요청
   *
   * @template T 응답 데이터 타입
   * @template D 요청 데이터 타입
   * @param url API 엔드포인트
   * @param data 요청 본문 데이터
   * @returns Promise<T> 응답 데이터
   */
  post: async <T, D = unknown>(url: string, data?: D): Promise<T> => {
    const response = await apiClient.post<T>(url, data);
    return response.data;
  },

  /**
   * PATCH 요청
   *
   * @template T 응답 데이터 타입
   * @template D 요청 데이터 타입
   * @param url API 엔드포인트
   * @param data 요청 본문 데이터
   * @returns Promise<T> 응답 데이터
   */
  patch: async <T, D = unknown>(url: string, data?: D): Promise<T> => {
    const response = await apiClient.patch<T>(url, data);
    return response.data;
  },

  /**
   * DELETE 요청
   *
   * @template T 응답 데이터 타입
   * @param url API 엔드포인트
   * @returns Promise<T> 응답 데이터
   */
  delete: async <T>(url: string): Promise<T> => {
    const response = await apiClient.delete<T>(url);
    return response.data;
  },
};

export default apiClient;
