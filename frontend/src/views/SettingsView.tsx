import { useState, useEffect, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { RefreshCw, Save, AlertCircle, Settings } from 'lucide-react'
import {
  fetchConfigs,
  batchUpdateConfigs,
  resetAllConfigs,
  validateConfigValue,
  type ConfigValue,
} from '@/api/config.api'
import { CommonButton } from '@/core/components/CommonButton'
import { TradingSettingsForm } from '@/components/settings/TradingSettingsForm'
import { AISettingsForm } from '@/components/settings/AISettingsForm'
import { ResetSettingsButton } from '@/components/settings/ResetSettingsButton'
import { useToastHelpers } from '@/core/components/Toast'

export function SettingsView() {
  const queryClient = useQueryClient()
  const toast = useToastHelpers()

  // Local state for pending changes
  const [pendingChanges, setPendingChanges] = useState<Record<string, ConfigValue>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)

  // Fetch configs query
  const {
    data: configData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['configs'],
    queryFn: fetchConfigs,
    staleTime: 30000, // 30 seconds
  })

  // Batch update mutation
  const updateMutation = useMutation({
    mutationFn: batchUpdateConfigs,
    onSuccess: (result) => {
      if (result.failed.length > 0) {
        toast.warning(`일부 설정을 저장하지 못했습니다: ${result.failed.join(', ')}`)
      } else {
        toast.success('설정이 저장되었습니다')
      }
      // Clear pending changes
      setPendingChanges({})
      setHasUnsavedChanges(false)
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['configs'] })
    },
    onError: (err) => {
      toast.error(
        err instanceof Error ? err.message : '설정 저장에 실패했습니다'
      )
    },
  })

  // Reset mutation
  const resetMutation = useMutation({
    mutationFn: resetAllConfigs,
    onSuccess: () => {
      toast.success('설정이 기본값으로 초기화되었습니다')
      setPendingChanges({})
      setErrors({})
      setHasUnsavedChanges(false)
      queryClient.invalidateQueries({ queryKey: ['configs'] })
    },
    onError: (err) => {
      toast.error(
        err instanceof Error ? err.message : '설정 초기화에 실패했습니다'
      )
    },
  })

  // Handle config change
  const handleConfigChange = useCallback((key: string, value: ConfigValue) => {
    // Validate value
    const validation = validateConfigValue(key, value)
    if (!validation.valid && validation.error) {
      setErrors((prev) => ({ ...prev, [key]: validation.error! }))
      return
    }

    // Clear error if valid
    setErrors((prev) => {
      const newErrors = { ...prev }
      delete newErrors[key]
      return newErrors
    })

    // Track pending change
    setPendingChanges((prev) => ({ ...prev, [key]: value }))
    setHasUnsavedChanges(true)
  }, [])

  // Handle save
  const handleSave = useCallback(() => {
    if (Object.keys(errors).length > 0) {
      toast.error('유효성 검사 오류를 먼저 수정하세요')
      return
    }

    if (Object.keys(pendingChanges).length === 0) {
      toast.info('변경된 설정이 없습니다')
      return
    }

    updateMutation.mutate(pendingChanges)
  }, [pendingChanges, errors, updateMutation, toast])

  // Handle reset
  const handleReset = useCallback(async () => {
    await resetMutation.mutateAsync()
  }, [resetMutation])

  // Handle refresh
  const handleRefresh = useCallback(() => {
    setPendingChanges({})
    setErrors({})
    setHasUnsavedChanges(false)
    refetch()
  }, [refetch])

  // Warn about unsaved changes on navigation
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault()
        e.returnValue = ''
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [hasUnsavedChanges])

  // Merge config data with pending changes for display
  const displayConfigs: Record<string, ConfigValue> = {
    ...(configData?.configs || {}),
    ...pendingChanges,
  }

  // Error state
  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertCircle className="h-16 w-16 text-red-400 mb-4" />
        <h2 className="text-xl font-semibold text-white mb-2">
          설정을 불러올 수 없습니다
        </h2>
        <p className="text-gray-400 mb-4">
          {error instanceof Error
            ? error.message
            : '알 수 없는 오류가 발생했습니다'}
        </p>
        <CommonButton onClick={handleRefresh} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          다시 시도
        </CommonButton>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Settings className="h-7 w-7 text-primary" />
          <div>
            <h1 className="text-2xl font-bold text-white">설정</h1>
            <p className="text-sm text-gray-400">시스템 설정 관리</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <CommonButton
            onClick={handleRefresh}
            variant="outline"
            size="sm"
            className="gap-2"
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            새로고침
          </CommonButton>
        </div>
      </div>

      {/* Unsaved changes banner */}
      {hasUnsavedChanges && (
        <div className="bg-yellow-900/30 border border-yellow-500/50 rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center gap-2 text-yellow-200">
            <AlertCircle className="h-5 w-5" />
            <span className="text-sm">저장되지 않은 변경사항이 있습니다</span>
          </div>
          <div className="flex items-center gap-2">
            <CommonButton
              onClick={handleRefresh}
              variant="outline"
              size="sm"
              className="text-yellow-200 border-yellow-500/50 hover:bg-yellow-500/10"
            >
              변경 취소
            </CommonButton>
            <CommonButton
              onClick={handleSave}
              size="sm"
              disabled={updateMutation.isPending || Object.keys(errors).length > 0}
              className="bg-yellow-600 hover:bg-yellow-700"
            >
              {updateMutation.isPending ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  저장 중...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  저장
                </>
              )}
            </CommonButton>
          </div>
        </div>
      )}

      {/* Settings Forms */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Trading Settings */}
        <TradingSettingsForm
          configs={displayConfigs}
          isLoading={isLoading}
          onConfigChange={handleConfigChange}
          errors={errors}
        />

        {/* AI Settings */}
        <AISettingsForm
          configs={displayConfigs}
          isLoading={isLoading}
          onConfigChange={handleConfigChange}
          errors={errors}
        />
      </div>

      {/* Actions Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-700">
        <ResetSettingsButton
          onReset={handleReset}
          isResetting={resetMutation.isPending}
        />

        <div className="flex items-center gap-2">
          <CommonButton
            onClick={handleSave}
            disabled={
              updateMutation.isPending ||
              !hasUnsavedChanges ||
              Object.keys(errors).length > 0
            }
          >
            {updateMutation.isPending ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                저장 중...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                변경사항 저장
              </>
            )}
          </CommonButton>
        </div>
      </div>
    </div>
  )
}

export default SettingsView
