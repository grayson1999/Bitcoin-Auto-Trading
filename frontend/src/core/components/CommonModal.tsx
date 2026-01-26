import { useEffect, useRef, useCallback } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@core/components/ui/dialog'
import { cn } from '@core/utils'

interface CommonModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title?: string
  description?: string
  children: React.ReactNode
  footer?: React.ReactNode
  className?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
}

const sizeClasses = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
}

export function CommonModal({
  open,
  onOpenChange,
  title,
  description,
  children,
  footer,
  className,
  size = 'md',
}: CommonModalProps) {
  const historyPushedRef = useRef(false)

  const handlePopState = useCallback(() => {
    if (historyPushedRef.current) {
      historyPushedRef.current = false
      onOpenChange(false)
    }
  }, [onOpenChange])

  useEffect(() => {
    if (open) {
      history.pushState({ modal: true }, '')
      historyPushedRef.current = true
      window.addEventListener('popstate', handlePopState)
    }

    return () => {
      window.removeEventListener('popstate', handlePopState)
      if (historyPushedRef.current) {
        historyPushedRef.current = false
        history.back()
      }
    }
  }, [open, handlePopState])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={cn('bg-surface border-border', sizeClasses[size], className)}>
        {(title || description) && (
          <DialogHeader>
            {title && <DialogTitle>{title}</DialogTitle>}
            {description && <DialogDescription>{description}</DialogDescription>}
          </DialogHeader>
        )}
        <div className="py-4">{children}</div>
        {footer && <DialogFooter>{footer}</DialogFooter>}
      </DialogContent>
    </Dialog>
  )
}

export default CommonModal
