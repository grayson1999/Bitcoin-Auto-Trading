import { cn } from '@core/utils'
import { Button } from '@core/components/ui/button'
import type { SignalType } from '@/core/types'
import { TrendingUp, TrendingDown, Minus, List } from 'lucide-react'

type FilterValue = SignalType | 'all'

interface SignalTypeFilterProps {
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
    value: 'BUY',
    label: '매수',
    icon: <TrendingUp className="h-4 w-4" />,
    activeColor: 'bg-up text-white',
  },
  {
    value: 'SELL',
    label: '매도',
    icon: <TrendingDown className="h-4 w-4" />,
    activeColor: 'bg-down text-white',
  },
  {
    value: 'HOLD',
    label: '홀드',
    icon: <Minus className="h-4 w-4" />,
    activeColor: 'bg-neutral text-white',
  },
]

export function SignalTypeFilter({ value, onChange, className }: SignalTypeFilterProps) {
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

export default SignalTypeFilter
