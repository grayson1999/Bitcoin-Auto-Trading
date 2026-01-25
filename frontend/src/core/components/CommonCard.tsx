import { forwardRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@core/components/ui/card'
import { cn } from '@core/utils'

interface CommonCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string
  description?: string
  headerAction?: React.ReactNode
  noPadding?: boolean
}

export const CommonCard = forwardRef<HTMLDivElement, CommonCardProps>(
  ({ title, description, headerAction, noPadding, children, className, ...props }, ref) => {
    return (
      <Card ref={ref} className={cn('glass-card', className)} {...props}>
        {(title || description || headerAction) && (
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <div>
              {title && <CardTitle className="text-base font-semibold">{title}</CardTitle>}
              {description && (
                <CardDescription className="text-sm text-muted-foreground">
                  {description}
                </CardDescription>
              )}
            </div>
            {headerAction}
          </CardHeader>
        )}
        <CardContent className={cn(noPadding && 'p-0')}>{children}</CardContent>
      </Card>
    )
  }
)

CommonCard.displayName = 'CommonCard'

export default CommonCard
