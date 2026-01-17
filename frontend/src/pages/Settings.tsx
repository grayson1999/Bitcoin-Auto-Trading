/**
 * 설정 페이지 컴포넌트 (T077)
 *
 * 거래 파라미터와 위험 관리 설정을 구성합니다.
 * - 포지션 크기, 손절매 설정
 * - AI 모델 및 신호 주기 설정
 * - 변동성 임계값 설정
 */

import { useState, useEffect, type FC } from "react";
import { useConfig, useUpdateConfig, type SystemConfigUpdate } from "../hooks/useApi";

// === 상수 ===
const AI_MODELS = [
  { value: "gemini-2.5-pro", label: "Gemini 2.5 Pro (권장)" },
  { value: "gemini-2.5-flash", label: "Gemini 2.5 Flash" },
  { value: "gpt-4o", label: "GPT-4o" },
  { value: "gpt-4o-mini", label: "GPT-4o Mini" },
];

const CARD_CLASSES = "rounded-2xl glass-panel p-6";

/**
 * Settings 컴포넌트
 */
const Settings: FC = () => {
  const { data: config, isLoading, error } = useConfig();
  const updateMutation = useUpdateConfig();

  // 폼 상태
  const [formData, setFormData] = useState<SystemConfigUpdate>({});
  const [hasChanges, setHasChanges] = useState(false);

  // 설정 로드시 폼 초기화
  useEffect(() => {
    if (config) {
      setFormData({
        position_size_pct: config.position_size_pct,
        stop_loss_pct: config.stop_loss_pct,
        daily_loss_limit_pct: config.daily_loss_limit_pct,
        signal_interval_hours: config.signal_interval_hours,
        ai_model: config.ai_model,
        volatility_threshold_pct: config.volatility_threshold_pct,
      });
    }
  }, [config]);

  // 변경 감지
  useEffect(() => {
    if (config) {
      const changed =
        formData.position_size_pct !== config.position_size_pct ||
        formData.stop_loss_pct !== config.stop_loss_pct ||
        formData.daily_loss_limit_pct !== config.daily_loss_limit_pct ||
        formData.signal_interval_hours !== config.signal_interval_hours ||
        formData.ai_model !== config.ai_model ||
        formData.volatility_threshold_pct !== config.volatility_threshold_pct;
      setHasChanges(changed);
    }
  }, [formData, config]);

  // 입력 핸들러
  const handleChange = (field: keyof SystemConfigUpdate, value: number | string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  // 저장 핸들러
  const handleSave = () => {
    if (!hasChanges) return;

    const updates: SystemConfigUpdate = {};
    if (formData.position_size_pct !== config?.position_size_pct) {
      updates.position_size_pct = formData.position_size_pct;
    }
    if (formData.stop_loss_pct !== config?.stop_loss_pct) {
      updates.stop_loss_pct = formData.stop_loss_pct;
    }
    if (formData.daily_loss_limit_pct !== config?.daily_loss_limit_pct) {
      updates.daily_loss_limit_pct = formData.daily_loss_limit_pct;
    }
    if (formData.signal_interval_hours !== config?.signal_interval_hours) {
      updates.signal_interval_hours = formData.signal_interval_hours;
    }
    if (formData.ai_model !== config?.ai_model) {
      updates.ai_model = formData.ai_model;
    }
    if (formData.volatility_threshold_pct !== config?.volatility_threshold_pct) {
      updates.volatility_threshold_pct = formData.volatility_threshold_pct;
    }

    updateMutation.mutate(updates);
  };

  // 초기화 핸들러
  const handleReset = () => {
    if (config) {
      setFormData({
        position_size_pct: config.position_size_pct,
        stop_loss_pct: config.stop_loss_pct,
        daily_loss_limit_pct: config.daily_loss_limit_pct,
        signal_interval_hours: config.signal_interval_hours,
        ai_model: config.ai_model,
        volatility_threshold_pct: config.volatility_threshold_pct,
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-10 w-10 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
          <p className="mt-3 text-gray-500">설정 로딩 중...</p>
        </div>
      </div>
    );
  }

  if (error || !config) {
    return (
      <div className="rounded-lg bg-red-50 p-6 text-center">
        <p className="text-red-600">
          설정을 불러올 수 없습니다. 백엔드 서버를 확인하세요.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 페이지 헤더 */}
      <div>
        <h2 className="text-2xl font-bold text-white text-glow">설정</h2>
        <p className="text-dark-text-secondary mt-1">거래 파라미터와 위험 관리를 설정합니다.</p>
      </div>

      {/* 저장 결과 메시지 */}
      {updateMutation.isSuccess && (
        <div className="rounded-lg bg-green-50 p-4 text-center text-green-600">
          설정이 저장되었습니다.
        </div>
      )}
      {updateMutation.isError && (
        <div className="rounded-lg bg-red-50 p-4 text-center text-red-600">
          설정 저장 실패: {updateMutation.error?.message || "알 수 없는 오류"}
        </div>
      )}

      {/* 설정 카드들 */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* 리스크 관리 설정 */}
        <div className={CARD_CLASSES}>
          <h3 className="mb-4 text-lg font-semibold text-white">
            리스크 관리
          </h3>
          <div className="space-y-4">
            {/* 포지션 크기 */}
            <div>
              <label className="block text-sm font-medium text-dark-text-secondary flex items-center gap-1">
                포지션 크기 (%)
                <span className="relative group">
                  <span className="inline-flex items-center justify-center w-3.5 h-3.5 text-[10px] text-dark-text-muted border border-dark-text-muted rounded-full cursor-help hover:text-white hover:border-white transition-colors">
                    ?
                  </span>
                  <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 px-3 py-2 text-xs font-normal text-white bg-gray-900 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap z-10">
                    1회 주문 시 사용할 총 자산의 비율
                    <span className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></span>
                  </span>
                </span>
              </label>
              <input
                type="number"
                min={1}
                max={5}
                step={0.1}
                value={formData.position_size_pct ?? 2}
                onChange={(e) =>
                  handleChange("position_size_pct", Number(e.target.value))
                }
                className="mt-1 block w-full rounded-xl border border-dark-border px-3 py-2 text-white bg-dark-bg focus:border-banana-500 focus:outline-none focus:ring-1 focus:ring-banana-500 transition-all"
              />
              <p className="mt-1 text-xs text-dark-text-muted">
                주문당 자본의 비율 (1~5%)
              </p>
            </div>

            {/* 손절 임계값 */}
            <div>
              <label className="block text-sm font-medium text-dark-text-secondary">
                손절 임계값 (%)
              </label>
              <input
                type="number"
                min={3}
                max={10}
                step={0.1}
                value={formData.stop_loss_pct ?? 5}
                onChange={(e) =>
                  handleChange("stop_loss_pct", Number(e.target.value))
                }
                className="mt-1 block w-full rounded-xl border border-dark-border px-3 py-2 text-white bg-dark-bg focus:border-banana-500 focus:outline-none focus:ring-1 focus:ring-banana-500 transition-all"
              />
              <p className="mt-1 text-xs text-dark-text-muted">
                개별 손절 비율 (3~10%)
              </p>
            </div>

            {/* 일일 손실 한도 */}
            <div>
              <label className="block text-sm font-medium text-dark-text-secondary">
                일일 손실 한도 (%)
              </label>
              <input
                type="number"
                min={3}
                max={10}
                step={0.1}
                value={formData.daily_loss_limit_pct ?? 5}
                onChange={(e) =>
                  handleChange("daily_loss_limit_pct", Number(e.target.value))
                }
                className="mt-1 block w-full rounded-xl border border-dark-border px-3 py-2 text-white bg-dark-bg focus:border-banana-500 focus:outline-none focus:ring-1 focus:ring-banana-500 transition-all"
              />
              <p className="mt-1 text-xs text-dark-text-muted">
                하루 최대 손실 허용 비율 (3~10%)
              </p>
            </div>

            {/* 변동성 임계값 */}
            <div>
              <label className="block text-sm font-medium text-dark-text-secondary">
                변동성 임계값 (%)
              </label>
              <input
                type="number"
                min={1}
                max={10}
                step={0.1}
                value={formData.volatility_threshold_pct ?? 3}
                onChange={(e) =>
                  handleChange("volatility_threshold_pct", Number(e.target.value))
                }
                className="mt-1 block w-full rounded-xl border border-dark-border px-3 py-2 text-white bg-dark-bg focus:border-banana-500 focus:outline-none focus:ring-1 focus:ring-banana-500 transition-all"
              />
              <p className="mt-1 text-xs text-dark-text-muted">
                5분 내 이 비율 초과 변동 시 거래 중단 (1~10%)
              </p>
            </div>
          </div>
        </div>

        {/* AI 설정 */}
        <div className={CARD_CLASSES}>
          <h3 className="mb-4 text-lg font-semibold text-white">AI 설정</h3>
          <div className="space-y-4">
            {/* AI 모델 */}
            <div>
              <label className="block text-sm font-medium text-dark-text-secondary">
                AI 모델
              </label>
              <select
                value={formData.ai_model ?? "gemini-2.5-pro"}
                onChange={(e) => handleChange("ai_model", e.target.value)}
                className="mt-1 block w-full rounded-xl border border-dark-border px-3 py-2 text-white bg-dark-bg focus:border-banana-500 focus:outline-none focus:ring-1 focus:ring-banana-500 transition-all"
              >
                {AI_MODELS.map((model) => (
                  <option key={model.value} value={model.value}>
                    {model.label}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-dark-text-muted">
                매매 신호 생성에 사용할 AI 모델
              </p>
            </div>

            {/* 신호 생성 주기 */}
            <div>
              <label className="block text-sm font-medium text-dark-text-secondary">
                신호 생성 주기 (시간)
              </label>
              <select
                value={formData.signal_interval_hours ?? 1}
                onChange={(e) =>
                  handleChange("signal_interval_hours", Number(e.target.value))
                }
                className="mt-1 block w-full rounded-xl border border-dark-border px-3 py-2 text-white bg-dark-bg focus:border-banana-500 focus:outline-none focus:ring-1 focus:ring-banana-500 transition-all"
              >
                <option value={1}>1시간</option>
                <option value={2}>2시간</option>
                <option value={4}>4시간</option>
              </select>
              <p className="mt-1 text-xs text-dark-text-muted">
                AI 신호 자동 생성 간격
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 현재 상태 */}
      <div className={CARD_CLASSES}>
        <h3 className="mb-4 text-lg font-semibold text-white">현재 상태</h3>
        <div className="flex items-center gap-3">
          <span className="text-dark-text-secondary">거래 활성화:</span>
          {config.trading_enabled ? (
            <span className="inline-flex items-center rounded-full bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 text-sm font-medium text-emerald-400">
              활성
            </span>
          ) : (
            <span className="inline-flex items-center rounded-full bg-rose-500/10 border border-rose-500/20 px-3 py-1 text-sm font-medium text-rose-400">
              비활성
            </span>
          )}
        </div>
      </div>

      {/* 버튼들 */}
      <div className="flex justify-end gap-3">
        <button
          onClick={handleReset}
          disabled={!hasChanges}
          className="rounded-xl border border-dark-border px-4 py-2 text-sm font-medium text-dark-text-secondary hover:bg-white/5 focus:outline-none focus:ring-2 focus:ring-banana-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-all"
        >
          초기화
        </button>
        <button
          onClick={handleSave}
          disabled={!hasChanges || updateMutation.isPending}
          className="rounded-xl bg-banana-500 px-4 py-2 text-sm font-medium text-black hover:bg-banana-400 focus:outline-none focus:ring-2 focus:ring-banana-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 shadow-[0_0_15px_rgba(250,204,21,0.4)] transition-all hover:shadow-[0_0_20px_rgba(250,204,21,0.6)]"
        >
          {updateMutation.isPending ? "저장 중..." : "설정 저장"}
        </button>
      </div>
    </div>
  );
};

export default Settings;
