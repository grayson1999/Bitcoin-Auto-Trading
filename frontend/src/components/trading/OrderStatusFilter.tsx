import { cn } from '@core/utils'
import { Button } from '@core/components/ui/button'
import type { OrderStatus } from '@/core/types'
import { List, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react'

type FilterValue = OrderStatus | 'all'

interface OrderStatusFilterProps {
  value: FilterValue
  onChange: (value: FilterValue) => void
  className?: string
}

const filterOptions: Array<{
  value: FilterValue
  label: string
  icon: React.ReactNode
  activeColor: string
}> = [
  {
    value: 'all',
    label: '전체',
    icon: <List className="h-4 w-4" />,
    activeColor: 'bg-primary text-primary-foreground',
  },
  {
    value: 'PENDING',
    label: '대기',
    icon: <Clock className="h-4 w-4" />,
    activeColor: 'bg-yellow-500 text-white',
  },
  {
    value: 'EXECUTED',
    label: '체결',
    icon: <CheckCircle className="h-4 w-4" />,
    activeColor: 'bg-up text-white',
  },
  {
    value: 'CANCELLED',
    label: '취소',
    icon: <XCircle className="h-4 w-4" />,
    activeColor: 'bg-muted-foreground text-white',
  },
  {
    value: 'FAILED',
    label: '실패',
    icon: <AlertCircle className="h-4 w-4" />,
    activeColor: 'bg-down text-white',
  },
]

export function OrderStatusFilter({ value, onChange, className }: OrderStatusFilterProps) {
  return (
    <div className={cn('flex items-center gap-1 p-1 bg-muted rounded-lg', className)}>
      {filterOptions.map((option) => {
        const isActive = value === option.value

        return (
          <Button
            key={option.value}
            variant="ghost"
            size="sm"
            onClick={() => onChange(option.value)}
            className={cn(
              'h-8 px-3 gap-1.5 transition-colors',
              isActive ? option.activeColor : 'hover:bg-background/50'
            )}
          >
            {option.icon}
            <span className="hidden sm:inline">{option.label}</span>
          </Button>
        )
      })}
    </div>
  )
}

export default OrderStatusFilter
