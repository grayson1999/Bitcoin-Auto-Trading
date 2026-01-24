import { cn } from '@core/utils'
import { Button } from '@core/components/ui/button'
import { LayoutGrid, List } from 'lucide-react'

export type ViewMode = 'grid' | 'timeline'

interface ViewToggleProps {
  value: ViewMode
  onChange: (value: ViewMode) => void
  className?: string
}

const viewOptions: Array<{
  value: ViewMode
  label: string
  icon: React.ReactNode
}> = [
  {
    value: 'grid',
    label: '그리드',
    icon: <LayoutGrid className="h-4 w-4" />,
  },
  {
    value: 'timeline',
    label: '타임라인',
    icon: <List className="h-4 w-4" />,
  },
]

export function ViewToggle({ value, onChange, className }: ViewToggleProps) {
  return (
    <div className={cn('flex items-center gap-1 p-1 bg-muted rounded-lg', className)}>
      {viewOptions.map((option) => {
        const isActive = value === option.value

        return (
          <Button
            key={option.value}
            variant="ghost"
            size="sm"
            onClick={() => onChange(option.value)}
            className={cn(
              'h-8 px-3 gap-1.5 transition-colors',
              isActive && 'bg-background shadow-sm'
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

export default ViewToggle
