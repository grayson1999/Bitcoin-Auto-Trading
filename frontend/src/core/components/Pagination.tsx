import { Button } from '@core/components/ui/button'
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react'
import { cn } from '@core/utils'

interface PaginationProps {
  currentPage: number
  totalPages: number
  totalItems: number
  pageSize: number
  onPageChange: (page: number) => void
  className?: string
  showItemCount?: boolean
}

export function Pagination({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
  className,
  showItemCount = true,
}: PaginationProps) {
  const hasPrevPage = currentPage > 0
  const hasNextPage = currentPage < totalPages - 1

  const startItem = currentPage * pageSize + 1
  const endItem = Math.min((currentPage + 1) * pageSize, totalItems)

  const handleFirst = () => {
    if (hasPrevPage) {
      onPageChange(0)
    }
  }

  const handlePrev = () => {
    if (hasPrevPage) {
      onPageChange(currentPage - 1)
    }
  }

  const handleNext = () => {
    if (hasNextPage) {
      onPageChange(currentPage + 1)
    }
  }

  const handleLast = () => {
    if (hasNextPage) {
      onPageChange(totalPages - 1)
    }
  }

  return (
    <div className={cn('flex items-center justify-between', className)}>
      {showItemCount && (
        <p className="text-sm text-muted-foreground">
          {totalItems === 0 ? (
            '항목 없음'
          ) : (
            <>
              전체 <span className="font-medium">{totalItems}</span>개 중{' '}
              <span className="font-medium">{startItem}-{endItem}</span>개 표시
            </>
          )}
        </p>
      )}

      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          onClick={handleFirst}
          disabled={!hasPrevPage}
        >
          <ChevronsLeft className="h-4 w-4" />
          <span className="sr-only">처음</span>
        </Button>
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          onClick={handlePrev}
          disabled={!hasPrevPage}
        >
          <ChevronLeft className="h-4 w-4" />
          <span className="sr-only">이전</span>
        </Button>

        <span className="text-sm text-muted-foreground px-3 min-w-[80px] text-center">
          {totalPages === 0 ? (
            '0 / 0'
          ) : (
            <>
              <span className="font-medium">{currentPage + 1}</span> / {totalPages}
            </>
          )}
        </span>

        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          onClick={handleNext}
          disabled={!hasNextPage}
        >
          <ChevronRight className="h-4 w-4" />
          <span className="sr-only">다음</span>
        </Button>
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          onClick={handleLast}
          disabled={!hasNextPage}
        >
          <ChevronsRight className="h-4 w-4" />
          <span className="sr-only">마지막</span>
        </Button>
      </div>
    </div>
  )
}

export default Pagination
