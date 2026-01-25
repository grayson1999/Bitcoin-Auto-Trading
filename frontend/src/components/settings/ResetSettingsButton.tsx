import { useState } from 'react'
import { Button } from '@/core/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/core/components/ui/dialog'
import { RotateCcw, AlertTriangle } from 'lucide-react'

interface ResetSettingsButtonProps {
  onReset: () => Promise<void>
  isResetting?: boolean
}

export function ResetSettingsButton({ onReset, isResetting }: ResetSettingsButtonProps) {
  const [isOpen, setIsOpen] = useState(false)

  const handleReset = async () => {
    await onReset()
    setIsOpen(false)
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          className="text-yellow-400 border-yellow-400/50 hover:bg-yellow-400/10"
          disabled={isResetting}
        >
          <RotateCcw className="h-4 w-4 mr-2" />
          기본값으로 초기화
        </Button>
      </DialogTrigger>
      <DialogContent className="bg-gray-900 border-gray-700">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-yellow-400">
            <AlertTriangle className="h-5 w-5" />
            설정 초기화
          </DialogTitle>
          <DialogDescription className="text-gray-400">
            모든 설정이 기본값으로 초기화됩니다. 이 작업은 되돌릴 수 없습니다.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <div className="bg-gray-800/50 rounded-lg p-4 space-y-2">
            <p className="text-sm text-gray-300">초기화될 설정:</p>
            <ul className="text-xs text-gray-400 space-y-1 ml-4 list-disc">
              <li>포지션 크기 (최소/최대)</li>
              <li>손절매 비율</li>
              <li>일일 손실 한도</li>
              <li>변동성 임계값</li>
              <li>AI 모델</li>
              <li>AI 신호 주기</li>
            </ul>
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={() => setIsOpen(false)}
            className="border-gray-600"
          >
            취소
          </Button>
          <Button
            variant="destructive"
            onClick={handleReset}
            disabled={isResetting}
            className="bg-yellow-600 hover:bg-yellow-700"
          >
            {isResetting ? (
              <>
                <RotateCcw className="h-4 w-4 mr-2 animate-spin" />
                초기화 중...
              </>
            ) : (
              <>
                <RotateCcw className="h-4 w-4 mr-2" />
                초기화
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
