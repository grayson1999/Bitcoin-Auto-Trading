import type { AxiosError } from 'axios'

const ERROR_MESSAGES: Record<number, string> = {
  400: '잘못된 요청입니다.',
  401: '세션이 만료되었습니다. 다시 로그인해 주세요.',
  403: '접근 권한이 없습니다.',
  404: '요청한 데이터를 찾을 수 없습니다.',
  429: '요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.',
  500: '서버 오류가 발생했습니다.',
  503: '서비스를 일시적으로 사용할 수 없습니다.',
}

const RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504]

export class ApiError extends Error {
  public readonly status: number
  public readonly retryable: boolean
  public readonly originalError?: AxiosError

  constructor(status: number, message: string, retryable = false, originalError?: AxiosError) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.retryable = retryable
    this.originalError = originalError
  }

  static fromAxiosError(error: AxiosError): ApiError {
    const status = error.response?.status ?? 0
    const serverMessage = (error.response?.data as { message?: string })?.message
    const message = serverMessage || ERROR_MESSAGES[status] || '알 수 없는 오류가 발생했습니다.'
    const retryable = RETRYABLE_STATUS_CODES.includes(status)

    return new ApiError(status, message, retryable, error)
  }

  static isNetworkError(error: unknown): boolean {
    return error instanceof Error && error.message === 'Network Error'
  }

  static createNetworkError(): ApiError {
    return new ApiError(0, '네트워크 연결을 확인해 주세요.', true)
  }

  static createTimeoutError(): ApiError {
    return new ApiError(408, '요청 시간이 초과되었습니다. 다시 시도해 주세요.', true)
  }

  toJSON(): { status: number; message: string; retryable: boolean } {
    return {
      status: this.status,
      message: this.message,
      retryable: this.retryable,
    }
  }
}

export default ApiError
