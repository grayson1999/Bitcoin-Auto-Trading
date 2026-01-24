import { AlertCircle, RefreshCw } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@core/components/ui/alert'
import { Button } from '@core/components/ui/button'
import { cn } from '@core/utils'

interface ErrorMessageProps {
  title?: string
  message: string
  onRetry?: () => void
  className?: string
}

export function ErrorMessage({
  title = '오류가 발생했습니다',
  message,
  onRetry,
  className,
}: ErrorMessageProps) {
  return (
    <Alert variant="destructive" className={cn('bg-destructive/10 border-destructive/50', className)}>
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription className="flex items-center justify-between gap-4">
        <span>{message}</span>
        {onRetry && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="shrink-0"
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            다시 시도
          </Button>
        )}
      </AlertDescription>
    </Alert>
  )
}

export default ErrorMessage
