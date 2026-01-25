import { useEffect, useState, createContext, useContext, useCallback } from 'react'
import { cn } from '@/core/utils'
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react'

// ============================================================================
// Types
// ============================================================================

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface Toast {
  id: string
  type: ToastType
  message: string
  duration?: number
}

interface ToastContextValue {
  toasts: Toast[]
  addToast: (type: ToastType, message: string, duration?: number) => void
  removeToast: (id: string) => void
}

// ============================================================================
// Context
// ============================================================================

const ToastContext = createContext<ToastContextValue | null>(null)

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

// ============================================================================
// Provider
// ============================================================================

interface ToastProviderProps {
  children: React.ReactNode
}

export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = useCallback(
    (type: ToastType, message: string, duration: number = 3000) => {
      const id = `toast-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`
      const toast: Toast = { id, type, message, duration }
      setToasts((prev) => [...prev, toast])
    },
    []
  )

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  )
}

// ============================================================================
// Toast Container
// ============================================================================

interface ToastContainerProps {
  toasts: Toast[]
  onRemove: (id: string) => void
}

function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  )
}

// ============================================================================
// Toast Item
// ============================================================================

interface ToastItemProps {
  toast: Toast
  onRemove: (id: string) => void
}

function ToastItem({ toast, onRemove }: ToastItemProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [isExiting, setIsExiting] = useState(false)

  useEffect(() => {
    // Animate in
    requestAnimationFrame(() => setIsVisible(true))

    // Auto-dismiss
    if (toast.duration && toast.duration > 0) {
      const timer = setTimeout(() => {
        setIsExiting(true)
        setTimeout(() => onRemove(toast.id), 200)
      }, toast.duration)
      return () => clearTimeout(timer)
    }
  }, [toast.id, toast.duration, onRemove])

  const handleClose = () => {
    setIsExiting(true)
    setTimeout(() => onRemove(toast.id), 200)
  }

  const Icon = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info,
  }[toast.type]

  const colorClasses = {
    success: 'bg-green-900/90 border-green-500/50 text-green-200',
    error: 'bg-red-900/90 border-red-500/50 text-red-200',
    warning: 'bg-yellow-900/90 border-yellow-500/50 text-yellow-200',
    info: 'bg-blue-900/90 border-blue-500/50 text-blue-200',
  }[toast.type]

  const iconColorClasses = {
    success: 'text-green-400',
    error: 'text-red-400',
    warning: 'text-yellow-400',
    info: 'text-blue-400',
  }[toast.type]

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-4 rounded-lg border shadow-lg backdrop-blur-sm',
        'transform transition-all duration-200 ease-out',
        colorClasses,
        isVisible && !isExiting ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'
      )}
      role="alert"
    >
      <Icon className={cn('h-5 w-5 flex-shrink-0 mt-0.5', iconColorClasses)} />
      <p className="flex-1 text-sm">{toast.message}</p>
      <button
        onClick={handleClose}
        className="flex-shrink-0 p-1 rounded hover:bg-white/10 transition-colors"
        aria-label="닫기"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}

// ============================================================================
// Convenience hook for common toast patterns
// ============================================================================

export function useToastHelpers() {
  const { addToast } = useToast()

  return {
    success: (message: string, duration?: number) =>
      addToast('success', message, duration),
    error: (message: string, duration?: number) =>
      addToast('error', message, duration),
    warning: (message: string, duration?: number) =>
      addToast('warning', message, duration),
    info: (message: string, duration?: number) =>
      addToast('info', message, duration),
  }
}
