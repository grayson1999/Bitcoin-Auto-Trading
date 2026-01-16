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
 * 개발 모드에서 요청 로그를 출력합니다.
 */
apiClient.interceptors.request.use(
  (config) => {
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
 * - 오류: 상태 코드별 오류 처리 및 로깅
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError<ErrorResponse>) => {
    if (error.response) {
      // 서버 응답이 있는 경우
      const status = error.response.status;
      const message = error.response.data?.detail || "오류가 발생했습니다";

      console.error(`${LOG_PREFIX.ERROR} ${status}: ${message}`);

      // 특정 상태 코드에 대한 처리
      if (status === HTTP_STATUS.UNAUTHORIZED) {
        console.error("인증되지 않은 접근");
      } else if (status === HTTP_STATUS.SERVICE_UNAVAILABLE) {
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
