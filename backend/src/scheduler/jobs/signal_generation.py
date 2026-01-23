"""
신호 생성 스케줄러 작업

AI 매매 신호 생성, 자동 매매 실행, 변동성 체크, 신호 성과 평가 작업을 정의합니다.
"""

from loguru import logger
from sqlalchemy import select

from src.database import async_session_factory
from src.entities import SignalType, TradingSignal


async def generate_trading_signal_job() -> None:
    """
    AI 매매 신호 생성 작업

    설정된 주기(기본 1시간)마다 AI 신호를 생성합니다.
    AI가 모든 기술적 지표와 시장 상황을 종합 분석합니다.

    AI 신호 규칙:
        - BUY: AI가 매수 적합으로 판단 (신뢰도 기반 포지션 사이징)
        - SELL: AI가 매도 적합으로 판단 (손절/익절 포함)
        - HOLD: 관망 권장

    처리 흐름:
        1. Upbit 잔고와 포지션 동기화
        2. SignalService로 AI 신호 생성
        3. 결과 DB 저장
        4. 신호가 BUY/SELL이면 신뢰도 기반 포지션 사이징으로 자동 매매 실행

    Note:
        신뢰도 기반 포지션 사이징:
        - 신뢰도 0.5: 자본의 1% (최소)
        - 신뢰도 0.9+: 자본의 3% (최대)
        AI의 "소량 매수" 판단은 낮은 신뢰도로 반영됩니다.
    """
    # 순환 참조 방지를 위한 지연 임포트
    from src.modules.signal.service import SignalService, SignalServiceError
    from src.modules.trading.order_validator import OrderBlockedReason
    from src.modules.trading.service import get_trading_service

    async with async_session_factory() as session:
        try:
            # 신호 생성 전 Upbit 잔고와 포지션 동기화
            trading_service = await get_trading_service(session)
            await trading_service.sync_position_from_upbit()
            await session.flush()
            logger.debug("신호 생성 전 포지션 동기화 완료")

            # SignalService로 신호 생성
            signal_service = SignalService(session)
            signal = await signal_service.generate_signal(force=True)

            logger.info(
                f"AI 신호 생성 완료: {signal.signal_type} "
                f"(신뢰도: {signal.confidence:.2f}, 모델: {signal.model_name})"
            )

            # 신호가 BUY 또는 SELL이면 신뢰도 기반 포지션 사이징으로 자동 매매 실행
            if signal.signal_type in (SignalType.BUY.value, SignalType.SELL.value):
                logger.info(
                    f"자동 매매 실행 시작: signal_id={signal.id}, "
                    f"type={signal.signal_type}, confidence={signal.confidence}"
                )

                order_result = await trading_service.execute_from_signal(signal)

                if order_result.success:
                    if order_result.order:
                        logger.info(
                            f"자동 매매 완료: order_id={order_result.order.id}, "
                            f"status={order_result.order.status}, "
                            f"message={order_result.message}"
                        )
                    else:
                        logger.info(f"자동 매매 결과: {order_result.message}")
                else:
                    logger.warning(
                        f"자동 매매 실패: {order_result.message}, "
                        f"reason={order_result.blocked_reason}"
                    )

                    # 잔고 부족으로 주문 실패 시 신호에 실패 사유 기록
                    if (
                        order_result.blocked_reason
                        == OrderBlockedReason.INSUFFICIENT_BALANCE
                    ):
                        signal.reasoning = (
                            signal.reasoning or ""
                        ) + f" [주문 실패: {order_result.blocked_reason.value}]"
                        logger.info(f"잔고 부족 - 신호 {signal.id}에 실패 사유 기록")

            # 최종 커밋 (신호 생성 + 주문 실행 결과 모두 포함)
            await session.commit()

        except SignalServiceError as e:
            await session.rollback()
            logger.warning(f"AI 신호 생성 실패: {e}")

        except Exception as e:
            await session.rollback()
            logger.exception(f"AI 신호 생성 작업 오류: {e}")


async def execute_trading_from_signal_job(signal_id: int) -> None:
    """
    신호에 따른 자동 매매 실행 작업

    AI 신호가 BUY 또는 SELL인 경우 리스크 체크 후 주문을 실행합니다.

    처리 흐름:
        1. 신호 조회
        2. 거래 활성화 상태 확인
        3. 리스크 체크 (일일 손실 한도, 변동성, 포지션 크기)
        4. 잔고 확인
        5. 주문 실행
        6. 포지션 및 통계 업데이트

    Args:
        signal_id: 실행할 신호 ID
    """
    # 순환 참조 방지를 위한 지연 임포트
    from src.modules.trading.order_validator import OrderBlockedReason
    from src.modules.trading.service import get_trading_service

    async with async_session_factory() as session:
        try:
            # 1. 신호 조회
            stmt = select(TradingSignal).where(TradingSignal.id == signal_id)
            result = await session.execute(stmt)
            signal = result.scalar_one_or_none()

            if signal is None:
                logger.error(f"신호를 찾을 수 없음: signal_id={signal_id}")
                return

            logger.info(
                f"자동 매매 실행 시작: signal_id={signal_id}, "
                f"type={signal.signal_type}, confidence={signal.confidence}"
            )

            # 2. TradingService 생성 및 주문 실행
            trading_service = await get_trading_service(session)
            order_result = await trading_service.execute_from_signal(signal)

            if order_result.success:
                if order_result.order:
                    logger.info(
                        f"자동 매매 완료: order_id={order_result.order.id}, "
                        f"status={order_result.order.status}, "
                        f"message={order_result.message}"
                    )
                else:
                    logger.info(f"자동 매매 결과: {order_result.message}")
            else:
                logger.warning(
                    f"자동 매매 실패: {order_result.message}, "
                    f"reason={order_result.blocked_reason}"
                )

                # 잔고 부족으로 주문 실패 시 신호를 HOLD로 변환
                if (
                    order_result.blocked_reason
                    == OrderBlockedReason.INSUFFICIENT_BALANCE
                ):
                    signal.signal_type = SignalType.HOLD.value
                    signal.reasoning = (
                        signal.reasoning or ""
                    ) + " [잔고 부족으로 HOLD 처리]"
                    await session.commit()
                    logger.info(f"잔고 부족 - 신호 {signal_id}를 HOLD로 변환")

        except Exception as e:
            await session.rollback()
            logger.exception(f"자동 매매 작업 오류: {e}")


async def check_volatility_job() -> None:
    """
    변동성 모니터링 작업

    30초마다 실행되어 시장 변동성을 체크하고,
    임계값을 초과하면 자동으로 거래를 중단합니다.

    처리 흐름:
        1. RiskService 인스턴스 생성
        2. 최근 5분간의 변동성 계산
        3. 임계값 초과 시 거래 중단
        4. 변동성 정상화 시 별도 조치 없음 (수동 재개 필요)
    """
    # 순환 참조 방지를 위한 지연 임포트
    from src.modules.risk.service import RiskCheckResult, get_risk_service

    async with async_session_factory() as session:
        try:
            risk_service = get_risk_service(session)

            result, volatility_pct, message = await risk_service.check_volatility()

            if result == RiskCheckResult.BLOCKED:
                # 고변동성 감지 - 거래 중단
                logger.warning(f"고변동성 감지로 거래 중단: {volatility_pct:.2f}%")
                await risk_service.halt_trading(
                    f"고변동성 자동 감지: {volatility_pct:.2f}% (5분 내)"
                )
                await session.commit()

            elif result == RiskCheckResult.WARNING:
                # 경고 수준 - 로그만 기록
                logger.info(f"변동성 경고: {message}")

            # PASS는 로그 없음 (너무 많은 로그 방지)

        except Exception as e:
            await session.rollback()
            logger.exception(f"변동성 체크 작업 오류: {e}")


async def evaluate_signal_performance_job() -> None:
    """
    신호 성과 평가 작업

    4시간마다 실행되어 과거 신호의 성과를 평가합니다.

    처리 흐름:
        1. 4시간 이상 경과한 신호에 현재 가격 기록
        2. 24시간 이상 경과한 신호 최종 평가
        3. 정확도 및 수익률 계산
    """
    # 순환 참조 방지를 위한 지연 임포트
    from src.modules.signal import SignalPerformanceTracker

    async with async_session_factory() as session:
        try:
            tracker = SignalPerformanceTracker(session)

            # 미평가 신호 성과 평가
            evaluated_count = await tracker.evaluate_pending_signals()

            if evaluated_count > 0:
                logger.info(f"신호 성과 평가 완료: {evaluated_count}건")

                # 성과 요약 생성 및 로깅
                summary = await tracker.generate_performance_summary(limit=50)
                logger.info(
                    f"최근 성과 요약: "
                    f"총 {summary.total_signals}건, "
                    f"매수 정확도 {summary.buy_accuracy:.1f}%, "
                    f"매도 정확도 {summary.sell_accuracy:.1f}%"
                )

        except Exception as e:
            await session.rollback()
            logger.exception(f"신호 성과 평가 작업 오류: {e}")
