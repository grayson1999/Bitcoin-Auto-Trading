import { apiClient } from '@/core/api/client'
import type { Position, Balance, Order, OrderListResponse, OrderStatus } from '@/core/types'

interface OrderListParams {
  status?: OrderStatus | 'all'
  page?: number
  limit?: number
}

/** Fetch current position */
export async function fetchPosition(): Promise<Position | null> {
  const response = await apiClient.get<Position | null>('/trading/position')
  return response.data
}

/** Fetch account balance */
export async function fetchBalance(): Promise<Balance> {
  const response = await apiClient.get<Balance>('/trading/balance')
  return response.data
}

/** Fetch order list with pagination */
export async function fetchOrders(params: OrderListParams = {}): Promise<OrderListResponse> {
  const { status = 'all', page = 1, limit = 20 } = params
  const response = await apiClient.get<OrderListResponse>('/trading/orders', {
    params: {
      status: status === 'all' ? undefined : status,
      page,
      limit,
    },
  })
  return response.data
}

/** Fetch single order by ID */
export async function fetchOrderById(orderId: string): Promise<Order> {
  const response = await apiClient.get<Order>(`/trading/orders/${orderId}`)
  return response.data
}

/** Sync pending orders with exchange */
export async function syncPendingOrders(): Promise<{ synced: number }> {
  const response = await apiClient.post('/trading/orders/sync')
  return response.data
}
