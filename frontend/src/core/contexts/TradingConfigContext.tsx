import { createContext, useContext, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchTradingStatus, extractCurrencyFromTicker } from '@/api/config.api'

interface TradingConfig {
  ticker: string       // e.g., "KRW-SOL"
  currency: string     // e.g., "SOL"
  tradingEnabled: boolean
  isLoading: boolean
}

const TradingConfigContext = createContext<TradingConfig | null>(null)

interface TradingConfigProviderProps {
  children: ReactNode
}

export function TradingConfigProvider({ children }: TradingConfigProviderProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['tradingStatus'],
    queryFn: fetchTradingStatus,
    staleTime: 5 * 60 * 1000, // 5분간 캐시
    refetchInterval: 5 * 60 * 1000, // 5분마다 갱신
    retry: 3,
  })

  const config: TradingConfig = {
    ticker: data?.ticker || 'KRW-BTC',
    currency: data?.ticker ? extractCurrencyFromTicker(data.ticker) : 'BTC',
    tradingEnabled: data?.trading_enabled ?? false,
    isLoading,
  }

  return (
    <TradingConfigContext.Provider value={config}>
      {children}
    </TradingConfigContext.Provider>
  )
}

export function useTradingConfig(): TradingConfig {
  const context = useContext(TradingConfigContext)
  if (!context) {
    // Context 외부에서 사용 시 기본값 반환
    return {
      ticker: 'KRW-BTC',
      currency: 'BTC',
      tradingEnabled: false,
      isLoading: false,
    }
  }
  return context
}
