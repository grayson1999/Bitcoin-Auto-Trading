# src/trading/signal_generation/service.py

from . import chatgpt_wrapper
from src.trading.data_collection.dto import RealtimeData
from src.utils.logger import get_logger
from src.database.session import get_history_db
from src.database.models import SignalHistory

logger = get_logger(name="signal.service", log_file="signal_service.log")

class SignalGenerationService:
    """매매 신호 생성 비즈니스 로직을 담당하는 서비스"""

    def __init__(self, options=None):
        """서비스 초기화 시 AI 모델 관련 옵션을 설정할 수 있습니다."""
        self.options = options if options is not None else {}

    def generate_signal(self, realtime_data: RealtimeData) -> chatgpt_wrapper.SignalResponse:
        """
        실시간 데이터를 기반으로 ChatGPT API를 호출하여 매매 신호를 생성하고,
        그 결과를 데이터베이스에 저장합니다.

        :param realtime_data: 판단 근거가 될 실시간 데이터 DTO
        :return: 파싱된 매매 신호 응답 객체
        """
        logger.info("ChatGPT API를 통해 매매 신호 생성을 요청합니다.")
        try:
            signal_response = chatgpt_wrapper.send_signal_request(
                realtime_data=realtime_data,
                options=self.options
            )
            logger.info(f"매매 신호 수신 완료: {signal_response.signal} (신뢰도: {signal_response.confidence})")

            # 신호 이력 저장
            with get_history_db() as db:
                history = SignalHistory(
                    signal=signal_response.signal,
                    reason=signal_response.reason,
                    confidence=signal_response.confidence,
                    timestamp=signal_response.timestamp
                )
                db.add(history)
                db.commit()
            logger.info("매매 신호 이력을 데이터베이스에 저장했습니다.")

            return signal_response
        except Exception as e:
            logger.error(f"매매 신호 생성 중 예외 발생: {e}", exc_info=True)
            # 예외 발생 시, 기본 "hold" 신호를 반환하거나 또는 예외를 다시 발생시킬 수 있습니다.
            # 여기서는 안전을 위해 "parsing_error"와 유사한 형태로 반환합니다.
            return chatgpt_wrapper.SignalResponse(
                signal='error',
                reason=f'Signal generation failed: {e}',
                confidence=0.0
            )
