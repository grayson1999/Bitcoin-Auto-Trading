/**
 * 로그인 페이지 컴포넌트
 *
 * 사용자 인증을 위한 로그인 폼을 제공합니다.
 * - 이메일/비밀번호 입력
 * - 폼 유효성 검사
 * - 오류 메시지 표시 (401, 423, 429)
 */

import { AxiosError } from "axios";
import { FormEvent, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";

// === 상수 ===
const MIN_PASSWORD_LENGTH = 8;
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// HTTP 상태 코드
const HTTP_STATUS = {
  UNAUTHORIZED: 401,
  LOCKED: 423,
  TOO_MANY_REQUESTS: 429,
} as const;

// 에러 메시지
const ERROR_MESSAGES = {
  INVALID_CREDENTIALS: "이메일 또는 비밀번호가 올바르지 않습니다",
  ACCOUNT_LOCKED: "계정이 일시적으로 잠겼습니다. 잠시 후 다시 시도해주세요",
  TOO_MANY_REQUESTS: "요청이 너무 많습니다. 잠시 후 다시 시도해주세요",
  AUTH_SERVER_ERROR: "인증 서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요",
  INVALID_EMAIL: "올바른 이메일 형식을 입력해주세요",
  PASSWORD_TOO_SHORT: `비밀번호는 ${MIN_PASSWORD_LENGTH}자 이상이어야 합니다`,
} as const;

export default function Login() {
  const { login, isAuthenticated, isLoading: authLoading } = useAuth();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 폼 유효성 검사
  const validateForm = (): boolean => {
    if (!EMAIL_REGEX.test(email)) {
      setError(ERROR_MESSAGES.INVALID_EMAIL);
      return false;
    }

    if (password.length < MIN_PASSWORD_LENGTH) {
      setError(ERROR_MESSAGES.PASSWORD_TOO_SHORT);
      return false;
    }

    return true;
  };

  // 로그인 제출 처리
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      await login(email, password);
      // 로그인 성공 시 AuthContext가 상태를 업데이트하고
      // isAuthenticated가 true가 되어 자동 리다이렉트됨
    } catch (err) {
      if (err instanceof AxiosError) {
        const status = err.response?.status;
        const detail = err.response?.data?.detail;

        switch (status) {
          case HTTP_STATUS.UNAUTHORIZED:
            setError(ERROR_MESSAGES.INVALID_CREDENTIALS);
            break;
          case HTTP_STATUS.LOCKED:
            setError(ERROR_MESSAGES.ACCOUNT_LOCKED);
            break;
          case HTTP_STATUS.TOO_MANY_REQUESTS:
            setError(ERROR_MESSAGES.TOO_MANY_REQUESTS);
            break;
          default:
            setError(detail || ERROR_MESSAGES.AUTH_SERVER_ERROR);
        }
      } else {
        setError(ERROR_MESSAGES.AUTH_SERVER_ERROR);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // 인증 상태 로딩 중이면 스피너 표시
  if (authLoading) {
    return (
      <div className="min-h-screen bg-dark-bg flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-banana-400"></div>
      </div>
    );
  }

  // 이미 로그인된 상태면 원래 페이지 또는 대시보드로 리다이렉트
  if (isAuthenticated) {
    const from = (location.state as { from?: string })?.from || "/";
    return <Navigate to={from} replace />;
  }

  return (
    <div className="min-h-screen relative flex items-center justify-center px-4 overflow-hidden bg-dark-bg">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-dark-bg">
        <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-banana-500/10 blur-[100px] animate-pulse-slow"></div>
        <div className="absolute bottom-[-20%] right-[-10%] w-[600px] h-[600px] rounded-full bg-indigo-500/10 blur-[100px] animate-pulse-slow delay-1000"></div>
      </div>

      <div className="w-full max-w-md relative z-10">
        {/* 로고 및 제목 */}
        <div className="text-center mb-10">
          <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-banana-400 to-orange-500 flex items-center justify-center shadow-lg shadow-banana-500/20 ring-4 ring-black/20 transform hover:scale-105 transition-all duration-300">
            <span className="text-white font-bold text-4xl">A</span>
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight mb-2">AutoBitcoin</h1>
          <p className="text-dark-text-secondary text-sm font-medium">
            스마트한 비트코인 자동매매의 시작
          </p>
        </div>

        {/* 로그인 폼 */}
        <div className="bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 p-8 shadow-2xl shadow-black/50">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* 에러 메시지 */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 flex items-start gap-3">
                <div className="text-red-400 font-bold shrink-0">!</div>
                <div className="text-red-400 text-sm font-medium leading-relaxed">{error}</div>
              </div>
            )}

            <div className="space-y-5">
              {/* 이메일 입력 */}
              <div>
                <label
                  htmlFor="email"
                  className="block text-xs font-semibold text-dark-text-secondary uppercase tracking-wider mb-2 ml-1"
                >
                  이메일
                </label>
                <div className="relative group">
                  <input
                    type="email"
                    id="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="email@example.com"
                    autoComplete="email"
                    required
                    disabled={isSubmitting}
                    className="w-full px-5 py-4 bg-black/20 border border-white/5 rounded-xl text-white placeholder-white/20 focus:outline-none focus:bg-black/30 focus:border-banana-400/50 focus:ring-1 focus:ring-banana-400/50 transition-all duration-300 disabled:opacity-50"
                  />
                  <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent scale-x-50 group-hover:scale-x-100 transition-transform duration-500" />
                </div>
              </div>

              {/* 비밀번호 입력 */}
              <div>
                <label
                  htmlFor="password"
                  className="block text-xs font-semibold text-dark-text-secondary uppercase tracking-wider mb-2 ml-1"
                >
                  비밀번호
                </label>
                <div className="relative group">
                  <input
                    type="password"
                    id="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    autoComplete="current-password"
                    required
                    disabled={isSubmitting}
                    className="w-full px-5 py-4 bg-black/20 border border-white/5 rounded-xl text-white placeholder-white/20 focus:outline-none focus:bg-black/30 focus:border-banana-400/50 focus:ring-1 focus:ring-banana-400/50 transition-all duration-300 disabled:opacity-50"
                  />
                  <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent scale-x-50 group-hover:scale-x-100 transition-transform duration-500" />
                </div>
              </div>
            </div>

            {/* 로그인 버튼 */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-4 px-6 bg-gradient-to-r from-banana-400 to-orange-500 hover:from-banana-500 hover:to-orange-600 text-white font-bold text-lg rounded-xl transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none shadow-lg shadow-banana-500/25 hover:shadow-banana-500/40"
            >
              {isSubmitting ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span>로그인 중...</span>
                </div>
              ) : (
                "로그인"
              )}
            </button>
          </form>
        </div>

        {/* 푸터 */}
        <div className="text-center mt-8">
          <p className="text-[10px] text-white/20 font-medium tracking-wide">
            © {new Date().getFullYear()} AutoBitcoin. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
}
