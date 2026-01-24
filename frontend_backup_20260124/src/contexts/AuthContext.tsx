/**
 * 인증 컨텍스트 모듈
 *
 * React Context를 사용하여 애플리케이션 전체의 인증 상태를 관리합니다.
 * - 로그인/로그아웃 기능
 * - 토큰 저장 및 자동 갱신
 * - localStorage 영속성
 */

import axios from "axios";
import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

// === 상수 ===
const AUTH_STORAGE_KEY = "auth";
const TOKEN_REFRESH_INTERVAL_MS = 14 * 60 * 1000; // 14분 (토큰 만료 1분 전)
const DEFAULT_AUTH_API_URL = "http://localhost:9000";
const AUTH_API_URL =
  import.meta.env.VITE_AUTH_API_URL ?? DEFAULT_AUTH_API_URL;

// === HTTP 상태 코드 상수 ===
const HTTP_STATUS = {
  UNAUTHORIZED: 401,
  LOCKED: 423,
  TOO_MANY_REQUESTS: 429,
  SERVICE_UNAVAILABLE: 503,
} as const;

// === 타입 정의 ===
export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

interface StoredAuth {
  accessToken: string;
  refreshToken: string;
  user: User;
  expiresAt: number;
}

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

interface RefreshResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

interface AuthContextValue {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  authError: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<boolean>;
  clearAuthError: () => void;
}

// === Auth API 클라이언트 ===
const authApi = axios.create({
  baseURL: `${AUTH_API_URL}/api/v1`,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// === 컨텍스트 생성 ===
const AuthContext = createContext<AuthContextValue | null>(null);

// === localStorage 유틸리티 ===
function loadStoredAuth(): StoredAuth | null {
  try {
    const stored = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!stored) return null;
    return JSON.parse(stored) as StoredAuth;
  } catch {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    return null;
  }
}

function saveStoredAuth(auth: StoredAuth): void {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(auth));
}

function clearStoredAuth(): void {
  localStorage.removeItem(AUTH_STORAGE_KEY);
}

// === AuthProvider 컴포넌트 ===
interface AuthProviderProps {
  children: ReactNode;
}

/**
 * 사용자 친화적 오류 메시지 반환
 * Auth Server 연결 오류를 적절한 메시지로 변환
 */
function getAuthErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    // 네트워크 오류 (Auth Server 연결 불가)
    if (!error.response) {
      return "인증 서버에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.";
    }

    const status = error.response.status;
    const detail = (error.response.data as { detail?: string })?.detail;

    // HTTP 상태 코드별 메시지
    switch (status) {
      case HTTP_STATUS.UNAUTHORIZED:
        return "이메일 또는 비밀번호가 올바르지 않습니다.";
      case HTTP_STATUS.LOCKED:
        return "계정이 잠겼습니다. 15분 후 다시 시도해 주세요.";
      case HTTP_STATUS.TOO_MANY_REQUESTS:
        return "요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.";
      case HTTP_STATUS.SERVICE_UNAVAILABLE:
        return "인증 서비스가 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해 주세요.";
      default:
        return detail || "로그인 중 오류가 발생했습니다.";
    }
  }

  return "알 수 없는 오류가 발생했습니다.";
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [tokens, setTokens] = useState<AuthTokens | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);
  const refreshTimerRef = useRef<number | null>(null);

  const isAuthenticated = useMemo(() => !!user && !!tokens, [user, tokens]);

  // 인증 오류 초기화
  const clearAuthError = useCallback(() => {
    setAuthError(null);
  }, []);

  // 토큰 갱신 타이머 설정
  const startRefreshTimer = useCallback(() => {
    // 기존 타이머 정리
    if (refreshTimerRef.current) {
      clearInterval(refreshTimerRef.current);
    }

    // 14분마다 토큰 갱신
    refreshTimerRef.current = window.setInterval(async () => {
      if (tokens?.refreshToken) {
        try {
          const response = await authApi.post<RefreshResponse>("/auth/refresh", {
            refresh_token: tokens.refreshToken,
          });

          const newAccessToken = response.data.access_token;
          const newExpiresAt = Date.now() + response.data.expires_in * 1000;

          setTokens((prev) =>
            prev ? { ...prev, accessToken: newAccessToken } : null
          );

          // localStorage 업데이트
          const stored = loadStoredAuth();
          if (stored) {
            saveStoredAuth({
              ...stored,
              accessToken: newAccessToken,
              expiresAt: newExpiresAt,
            });
          }

          if (import.meta.env.DEV) {
            console.log("[Auth] 토큰 자동 갱신 완료");
          }
        } catch (error) {
          console.error("[Auth] 토큰 자동 갱신 실패:", error);
          // 갱신 실패 시 로그아웃
          clearStoredAuth();
          setUser(null);
          setTokens(null);
          if (refreshTimerRef.current) {
            clearInterval(refreshTimerRef.current);
          }
        }
      }
    }, TOKEN_REFRESH_INTERVAL_MS);
  }, [tokens?.refreshToken]);

  // 토큰 갱신 함수 (외부 호출용)
  const refreshAccessToken = useCallback(async (): Promise<boolean> => {
    if (!tokens?.refreshToken) return false;

    try {
      const response = await authApi.post<RefreshResponse>("/auth/refresh", {
        refresh_token: tokens.refreshToken,
      });

      const newAccessToken = response.data.access_token;
      const newExpiresAt = Date.now() + response.data.expires_in * 1000;

      setTokens((prev) =>
        prev ? { ...prev, accessToken: newAccessToken } : null
      );

      // localStorage 업데이트
      const stored = loadStoredAuth();
      if (stored) {
        saveStoredAuth({
          ...stored,
          accessToken: newAccessToken,
          expiresAt: newExpiresAt,
        });
      }

      return true;
    } catch {
      return false;
    }
  }, [tokens?.refreshToken]);

  // 로그인 함수
  const login = useCallback(
    async (email: string, password: string): Promise<void> => {
      // 이전 오류 초기화
      setAuthError(null);

      try {
        const response = await authApi.post<LoginResponse>("/auth/login", {
          email,
          password,
        });

        const { access_token, refresh_token, expires_in, user: userData } = response.data;

        const newTokens: AuthTokens = {
          accessToken: access_token,
          refreshToken: refresh_token,
        };

        const expiresAt = Date.now() + expires_in * 1000;

        // 상태 업데이트
        setUser(userData);
        setTokens(newTokens);

        // localStorage에 저장
        saveStoredAuth({
          accessToken: access_token,
          refreshToken: refresh_token,
          user: userData,
          expiresAt,
        });

        // 토큰 갱신 타이머 시작
        startRefreshTimer();

        if (import.meta.env.DEV) {
          console.log("[Auth] 로그인 성공:", userData.email);
        }
      } catch (error) {
        const errorMessage = getAuthErrorMessage(error);
        setAuthError(errorMessage);

        if (import.meta.env.DEV) {
          console.error("[Auth] 로그인 실패:", errorMessage, error);
        }

        throw error;
      }
    },
    [startRefreshTimer]
  );

  // 로그아웃 함수
  const logout = useCallback(async (): Promise<void> => {
    // 타이머 정리
    if (refreshTimerRef.current) {
      clearInterval(refreshTimerRef.current);
      refreshTimerRef.current = null;
    }

    // Auth Server에 로그아웃 요청 (실패해도 로컬 정리)
    if (tokens?.accessToken && tokens?.refreshToken) {
      try {
        await authApi.post(
          "/auth/logout",
          { refresh_token: tokens.refreshToken },
          {
            headers: {
              Authorization: `Bearer ${tokens.accessToken}`,
            },
          }
        );
      } catch (error) {
        console.error("[Auth] 로그아웃 API 호출 실패:", error);
      }
    }

    // 로컬 상태 및 스토리지 정리
    clearStoredAuth();
    setUser(null);
    setTokens(null);

    if (import.meta.env.DEV) {
      console.log("[Auth] 로그아웃 완료");
    }
  }, [tokens?.accessToken, tokens?.refreshToken]);

  // 앱 로드 시 저장된 인증 상태 복원
  useEffect(() => {
    const restoreAuth = async () => {
      const stored = loadStoredAuth();

      if (stored) {
        // 토큰 만료 여부 확인
        if (stored.expiresAt > Date.now()) {
          setUser(stored.user);
          setTokens({
            accessToken: stored.accessToken,
            refreshToken: stored.refreshToken,
          });

          if (import.meta.env.DEV) {
            console.log("[Auth] 저장된 인증 상태 복원:", stored.user.email);
          }
        } else {
          // 만료된 토큰 - 리프레시 시도
          try {
            const response = await authApi.post<RefreshResponse>("/auth/refresh", {
              refresh_token: stored.refreshToken,
            });

            const newAccessToken = response.data.access_token;
            const newExpiresAt = Date.now() + response.data.expires_in * 1000;

            setUser(stored.user);
            setTokens({
              accessToken: newAccessToken,
              refreshToken: stored.refreshToken,
            });

            saveStoredAuth({
              ...stored,
              accessToken: newAccessToken,
              expiresAt: newExpiresAt,
            });

            if (import.meta.env.DEV) {
              console.log("[Auth] 토큰 갱신 후 인증 상태 복원");
            }
          } catch {
            // 갱신 실패 - 로그아웃 상태로
            clearStoredAuth();
            if (import.meta.env.DEV) {
              console.log("[Auth] 토큰 갱신 실패 - 로그아웃 상태");
            }
          }
        }
      }

      setIsLoading(false);
    };

    restoreAuth();
  }, []);

  // 인증 상태 변경 시 타이머 관리
  useEffect(() => {
    if (isAuthenticated) {
      startRefreshTimer();
    }

    return () => {
      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current);
      }
    };
  }, [isAuthenticated, startRefreshTimer]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      tokens,
      isAuthenticated,
      isLoading,
      authError,
      login,
      logout,
      refreshAccessToken,
      clearAuthError,
    }),
    [user, tokens, isAuthenticated, isLoading, authError, login, logout, refreshAccessToken, clearAuthError]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// === useAuth 훅 ===
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return context;
}

export default AuthContext;
