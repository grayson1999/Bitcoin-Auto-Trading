/**
 * React 오류 경계 컴포넌트
 *
 * 하위 컴포넌트에서 발생하는 JavaScript 오류를 포착하여
 * 애플리케이션 전체가 충돌하는 것을 방지합니다.
 *
 * 기능:
 * - 렌더링 오류 포착 및 로깅
 * - 사용자 친화적인 오류 UI 표시
 * - 오류 복구 (페이지 새로고침)
 */

import { Component, ErrorInfo, ReactNode } from "react";
import { ExclamationTriangleIcon } from "@heroicons/react/24/outline";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * 오류 경계 클래스 컴포넌트
 *
 * React의 componentDidCatch 생명주기를 사용하여
 * 하위 컴포넌트 트리의 오류를 포착합니다.
 */
class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  /**
   * 오류 발생 시 상태 업데이트
   *
   * 렌더링 중 오류가 발생하면 이 정적 메서드가 호출됩니다.
   */
  public static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  /**
   * 오류 로깅
   *
   * 오류와 컴포넌트 스택 정보를 콘솔에 로깅합니다.
   */
  public componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error("ErrorBoundary caught an error:", error);
    console.error("Component stack:", errorInfo.componentStack);
    this.setState({ errorInfo });
  }

  /**
   * 오류 상태 초기화 및 페이지 새로고침
   */
  private handleReload = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  /**
   * 홈으로 이동 (오류 상태 초기화)
   */
  private handleGoHome = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.href = "/";
  };

  public render(): ReactNode {
    if (this.state.hasError) {
      // 사용자 정의 fallback UI가 있으면 사용
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // 기본 오류 UI
      return (
        <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-gray-800 rounded-lg shadow-xl p-6 text-center">
            <div className="mx-auto w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mb-4">
              <ExclamationTriangleIcon className="w-8 h-8 text-red-500" />
            </div>
            <h1 className="text-xl font-semibold text-white mb-2">
              오류가 발생했습니다
            </h1>
            <p className="text-gray-400 mb-6">
              예기치 않은 오류로 인해 이 페이지를 표시할 수 없습니다.
            </p>

            {/* 개발 모드에서만 오류 상세 정보 표시 */}
            {import.meta.env.DEV && this.state.error && (
              <div className="mb-6 text-left">
                <div className="bg-gray-700/50 rounded-md p-3 overflow-auto max-h-40">
                  <p className="text-red-400 text-sm font-mono">
                    {this.state.error.message}
                  </p>
                  {this.state.errorInfo && (
                    <pre className="text-gray-400 text-xs mt-2 whitespace-pre-wrap">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  )}
                </div>
              </div>
            )}

            <div className="flex gap-3 justify-center">
              <button
                onClick={this.handleGoHome}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-md transition-colors"
              >
                홈으로
              </button>
              <button
                onClick={this.handleReload}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-md transition-colors"
              >
                새로고침
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
