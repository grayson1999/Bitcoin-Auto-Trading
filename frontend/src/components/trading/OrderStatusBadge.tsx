import { Badge } from '@core/components/ui/badge'
import { cn } from '@core/utils'
import type { OrderStatus } from '@/core/types'
import { CheckCircle, Clock, XCircle, AlertCircle } from 'lucide-react'

/** Status labels for display - exported for reuse (uppercase keys) */
export const ORDER_STATUS_LABELS: Record<OrderStatus, string> = {
  PENDING: '대기',
  EXECUTED: '체결',
  CANCELLED: '취소',
  FAILED: '실패',
}

interface OrderStatusBadgeProps {
  status: OrderStatus
  className?: string
}

const statusConfig: Record<
  OrderStatus,
  {
    label: string
    icon: React.ReactNode
    className: string
  }
> = {
  PENDING: {
    label: '대기',
    icon: <Clock className="h-3 w-3" />,
    className: 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30',
  },
  EXECUTED: {
    label: '체결',
    icon: <CheckCircle className="h-3 w-3" />,
    className: 'bg-up/20 text-up border-up/30',
  },
  CANCELLED: {
    label: '취소',
    icon: <XCircle className="h-3 w-3" />,
    className: 'bg-muted text-muted-foreground border-muted-foreground/30',
  },
  FAILED: {
    label: '실패',
    icon: <AlertCircle className="h-3 w-3" />,
    className: 'bg-down/20 text-down border-down/30',
  },
}

export function OrderStatusBadge({ status, className }: OrderStatusBadgeProps) {
  const config = statusConfig[status]

  return (
    <Badge
      variant="outline"
      className={cn(
        'gap-1 font-normal',
        config?.className,
        className
      )}
    >
      {config?.icon}
      {config?.label ?? status}
    </Badge>
  )
}

export default OrderStatusBadge
