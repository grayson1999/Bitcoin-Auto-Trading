import { CommonCard } from '@/core/components/CommonCard'
import { cn } from '@/core/utils'

interface SettingsSectionProps {
  title: string
  description?: string
  children: React.ReactNode
  className?: string
  headerAction?: React.ReactNode
}

export function SettingsSection({
  title,
  description,
  children,
  className,
  headerAction,
}: SettingsSectionProps) {
  return (
    <CommonCard
      title={title}
      description={description}
      headerAction={headerAction}
      className={cn('bg-surface', className)}
    >
      <div className="space-y-4">{children}</div>
    </CommonCard>
  )
}
