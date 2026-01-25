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
    <>
      {/* Desktop View: Table */}
      <div className={cn('hidden md:block rounded-lg border border-border overflow-x-auto', className)}>
        <Table className="min-w-[700px]">
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
            {orders.map((order) => (
              <DesktopRow key={order.id} order={order} />
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Mobile View: Cards */}
      <div className={cn('md:hidden space-y-4', className)}>
        {orders.map((order) => (
          <MobileOrderCard key={order.id} order={order} />
        ))}
      </div>
    </>
  )
}

function MobileOrderCard({ order }: { order: Order }) {
  const isBuy = order.side === 'BUY'
  const { displayPrice, displayQuantity, displayTotal } = getOrderDisplayValues(order)
  const typeLabel = order.order_type?.toUpperCase() === 'MARKET' ? '시장가' : '지정가'

  return (
    <div className="glass-card p-4 space-y-3">
      {/* Header: ID & Status */}
      <div className="flex items-start justify-between">
        <div className="flex flex-col">
          <span className="text-xs font-mono text-zinc-500">#{order.id}</span>
          <div className="flex items-center gap-2 mt-1">
            <span
              className={cn(
                'inline-flex items-center gap-1 text-sm font-bold',
                isBuy ? 'text-emerald-400' : 'text-rose-500'
              )}
            >
              {isBuy ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
              {isBuy ? '매수' : '매도'}
            </span>
            <span className="text-xs text-zinc-400 border-l border-zinc-700 pl-2">
              {typeLabel}
            </span>
          </div>
        </div>
        <OrderStatusBadge status={order.status} />
      </div>

      {/* Grid Details */}
      <div className="grid grid-cols-2 gap-3 py-3 border-y border-white/5">
        <div>
          <p className="text-xs text-zinc-500 mb-0.5">주문 가격</p>
          <p className="font-mono-num text-sm text-foreground">
            {displayPrice != null && displayPrice > 0 ? formatCurrency(displayPrice) : '-'}
          </p>
        </div>
        <div>
          <p className="text-xs text-zinc-500 mb-0.5">수량</p>
          <p className="font-mono-num text-sm text-foreground">
            {displayQuantity != null ? formatBTC(displayQuantity) : '-'}
          </p>
        </div>
        <div className="col-span-2">
          <p className="text-xs text-zinc-500 mb-0.5">총 금액</p>
          <p className="font-mono-num text-base font-medium text-foreground">
            {displayTotal != null && displayTotal > 0 ? formatCurrency(displayTotal) : '-'}
          </p>
        </div>
      </div>

      {/* Footer: Time */}
      <div className="text-xs text-zinc-500 text-right font-mono-num">
        {formatDateTime(order.created_at)}
      </div>
    </div>
  )
}

function DesktopRow({ order }: { order: Order }) {
  const isBuy = order.side === 'BUY'
  const { displayPrice, displayQuantity, displayTotal } = getOrderDisplayValues(order)
  const typeLabel = order.order_type?.toUpperCase() === 'MARKET' ? '시장가' : '지정가'

  return (
    <TableRow>
      <TableCell className="font-mono text-xs text-muted-foreground">
        {String(order.id).slice(0, 8)}...
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-muted-foreground">{typeLabel}</span>
          <div
            className={cn(
              'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium',
              isBuy ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-500'
            )}
          >
            {isBuy ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
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
}

function getOrderDisplayValues(order: Order) {
  const isBuy = order.side === 'BUY'

  // 가격: 체결가 우선 (0보다 커야 유효), 없으면 지정가
  const executedPrice = order.executed_price && order.executed_price > 0
    ? order.executed_price
    : null
  const displayPrice = executedPrice ?? order.price

  // 수량
  const displayQuantity = isBuy
    ? order.executed_amount
    : (order.executed_amount ?? order.amount)

  // 금액
  let displayTotal: number | null = null
  if (isBuy) {
    displayTotal = order.amount
  } else {
    // 매도: 체결가가 있으면 계산, 없으면 null
    if (displayPrice && displayQuantity) {
      displayTotal = displayPrice * displayQuantity
    }
  }

  return { displayPrice, displayQuantity, displayTotal }
}

export default OrderTable
