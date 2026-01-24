import { forwardRef } from 'react'
import { Button, type ButtonProps } from '@core/components/ui/button'
import { Loader2 } from 'lucide-react'
import { cn } from '@core/utils'

interface CommonButtonProps extends ButtonProps {
  isLoading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

export const CommonButton = forwardRef<HTMLButtonElement, CommonButtonProps>(
  ({ children, isLoading, leftIcon, rightIcon, disabled, className, ...props }, ref) => {
    return (
      <Button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(className)}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : leftIcon ? (
          <span className="mr-2">{leftIcon}</span>
        ) : null}
        {children}
        {rightIcon && !isLoading && <span className="ml-2">{rightIcon}</span>}
      </Button>
    )
  }
)

CommonButton.displayName = 'CommonButton'

export default CommonButton
