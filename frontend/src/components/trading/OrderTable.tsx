import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@core/components/ui/table'
import { OrderStatusBadge } from './OrderStatusBadge'
import { formatCurrency, formatBTC, formatDateTime } from '@core/utils/formatters'
import { cn } from '@core/utils'
import type { Order } from '@/core/types'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface OrderTableProps {
  orders: Order[]
  className?: string
}

export function OrderTable({ orders, className }: OrderTableProps) {
  return (
    <div className={cn('rounded-lg border border-border', className)}>
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50 hover:bg-muted/50">
            <TableHead className="w-[140px]">주문 ID</TableHead>
            <TableHead className="w-[140px]">타입</TableHead>
            <TableHead className="text-right">가격</TableHead>
            <TableHead className="text-right">수량</TableHead>
            <TableHead className="text-right">금액</TableHead>
            <TableHead className="w-[100px]">상태</TableHead>
            <TableHead className="w-[180px]">주문 시간</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {orders.map((order) => {
            const isBuy = order.side === 'BUY'

            // 가격: 체결가 우선 (0보다 커야 유효), 없으면 지정가
            const executedPrice = order.executed_price && order.executed_price > 0
              ? order.executed_price
              : null
            const displayPrice = executedPrice ?? order.price

            // 수량 (코인):
            // - 매수: executed_amount (체결된 코인 수량)
            // - 매도: amount (주문한 코인 수량) 또는 executed_amount
            const displayQuantity = isBuy
              ? order.executed_amount
              : (order.executed_amount ?? order.amount)

            // 금액 (KRW):
            // - 매수: amount (주문한 KRW 금액)
            // - 매도: 가격 * 수량 계산 (executed_price가 0이면 계산 불가)
            let displayTotal: number | null = null
            if (isBuy) {
              displayTotal = order.amount
            } else {
              // 매도: 체결가가 있으면 계산, 없으면 null
              if (displayPrice && displayQuantity) {
                displayTotal = displayPrice * displayQuantity
              }
            }

            // Map order type to Korean
            const typeLabel =
              order.order_type?.toUpperCase() === 'MARKET' ? '시장가' : '지정가'

            return (
              <TableRow key={order.id}>
                <TableCell className="font-mono text-xs text-muted-foreground">
                  {String(order.id).slice(0, 8)}...
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-muted-foreground">
                      {typeLabel}
                    </span>
                    <div
                      className={cn(
                        'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium',
                        isBuy
                          ? 'bg-up/20 text-up'
                          : 'bg-down/20 text-down'
                      )}
                    >
                      {isBuy ? (
                        <TrendingUp className="h-3 w-3" />
                      ) : (
                        <TrendingDown className="h-3 w-3" />
                      )}
                      {isBuy ? '매수' : '매도'}
                    </div>
                  </div>
                </TableCell>
                <TableCell className="text-right font-mono">
                  {displayPrice != null && displayPrice > 0 ? formatCurrency(displayPrice) : '-'}
                </TableCell>
                <TableCell className="text-right font-mono text-xs">
                  {displayQuantity != null ? formatBTC(displayQuantity) : '-'}
                </TableCell>
                <TableCell className="text-right font-mono">
                  {displayTotal != null && displayTotal > 0 ? formatCurrency(displayTotal) : '-'}
                </TableCell>
                <TableCell>
                  <OrderStatusBadge status={order.status} />
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {formatDateTime(order.created_at)}
                  {order.executed_at && order.status === 'EXECUTED' && (
                    <div className="text-[10px] text-muted-foreground/70 mt-0.5">
                      체결: {formatDateTime(order.executed_at)}
                    </div>
                  )}
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}

export default OrderTable
