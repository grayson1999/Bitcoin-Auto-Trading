"""
AI 매매 신호 생성 서비스 (동적 코인 지원 버전)

이 모듈은 Gemini AI를 사용하여 암호화폐 매매 신호를 생성하는 서비스를 제공합니다.
- 동적 코인 설정 (환경변수 TRADING_TICKER, TRADING_CURRENCY)
- 코인 유형별 프롬프트 템플릿 (메이저/밈코인/알트코인)
- 기술적 지표 분석 (RSI, MACD, 볼린저밴드, EMA, ATR)
- 멀티 타임프레임 분석 (1H, 4H, 1D, 1W)
- 시장 데이터 샘플링 (토큰 절감)
"""

import time
from datetime import datetime, timedelta
from decimal import Decimal

from loguru import logger
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.ai import AIClient, AIClientError, get_ai_client
from src.clients.upbit import (
    UpbitPrivateAPIError,
    UpbitPublicAPIError,
    get_upbit_private_api,
)
from src.config import settings
from src.config.constants import SIGNAL_COOLDOWN_MINUTES, SIGNAL_MARKET_DATA_HOURS
from src.config.logging import mask_sensitive_data
from src.entities import MarketData, TradingSignal
from src.entities.trading_signal import SignalType
from src.modules.market import (
    MultiTimeframeAnalyzer,
    MultiTimeframeResult,
    get_multi_timeframe_analyzer,
)
from src.modules.signal.classifier import get_coin_type
from src.modules.signal.parser import SignalResponseParser
from src.modules.signal.prompt import (
    PromptConfig,
    SignalPromptBuilder,
    get_config_for_coin,
    get_system_instruction,
)
from src.modules.signal.sampler import MarketDataSampler
from src.repositories.signal_repository import SignalRepository
from src.utils import UTC


class SignalServiceError(Exception):
    """신호 서비스 오류"""

    pass


class SignalService:
    """
    AI 매매 신호 생성 서비스 (동적 코인 지원)

    Gemini AI를 사용하여 설정된 코인의 시장 데이터를 분석하고
    Buy/Hold/Sell 신호를 생성합니다.

    특징:
    - 동적 코인 설정 (환경변수 기반)
    - 코인 유형별 최적화된 프롬프트 템플릿
    - 기술적 지표 분석 (RSI, MACD, 볼린저밴드, EMA, ATR)
    - 멀티 타임프레임 분석 (1H, 4H, 1D, 1W)
    - 시장 데이터 샘플링 (토큰 절감)

    사용 예시:
        service = SignalService(db_session)
        signal = await service.generate_signal()
        print(f"신호: {signal.signal_type}, 신뢰도: {signal.confidence}")
    """

    def __init__(
        self,
        db: AsyncSession,
        ai_client: AIClient | None = None,
        mtf_analyzer: MultiTimeframeAnalyzer | None = None,
    ):
        """
        신호 서비스 초기화

        Args:
            db: SQLAlchemy 비동기 세션
            ai_client: AI 클라이언트 (기본값: 싱글톤 사용)
            mtf_analyzer: 멀티 타임프레임 분석기 (기본값: 싱글톤 사용)
        """
        self.db = db
        self.ai_client = ai_client or get_ai_client()
        self.mtf_analyzer = mtf_analyzer or get_multi_timeframe_analyzer()

        # 동적 코인 설정
        self.ticker = settings.trading_ticker  # 예: "KRW-SOL"
        self.currency = settings.trading_currency  # 예: "SOL"
        self.coin_type = get_coin_type(self.currency)

        # 코인 유형에 따른 프롬프트 설정 (환경변수로 오버라이드 가능)
        base_config = get_config_for_coin(self.coin_type)
        self.prompt_config = PromptConfig(
            stop_loss_pct=settings.signal_stop_loss_pct,
            take_profit_pct=settings.signal_take_profit_pct,
            trailing_stop_pct=settings.signal_trailing_stop_pct,
            breakeven_pct=settings.signal_breakeven_pct,
            min_confidence_buy=base_config.min_confidence_buy,
            min_confluence_buy=base_config.min_confluence_buy,
            rsi_overbought=base_config.rsi_overbought,
            rsi_oversold=base_config.rsi_oversold,
            volatility_tolerance=base_config.volatility_tolerance,
        )

        # 프롬프트 빌더, 파서, 샘플러 초기화
        self._prompt_builder = SignalPromptBuilder(self.currency, self.prompt_config)
        self._response_parser = SignalResponseParser()
        self._signal_repo = SignalRepository(db)
        self._sampler = MarketDataSampler()

        logger.info(
            f"SignalService 초기화: {self.currency} ({self.coin_type.value}), "
            f"손절: {self.prompt_config.stop_loss_pct * 100:.1f}%, "
            f"익절: {self.prompt_config.take_profit_pct * 100:.1f}%"
        )

    async def generate_signal(
        self,
        force: bool = False,
        user_id: int | None = None,
    ) -> TradingSignal:
        """
        매매 신호 생성

        기술적 지표, 멀티 타임프레임 분석을 종합하여
        AI에게 분석을 요청하고 매매 신호를 생성합니다.

        Args:
            force: 쿨다운 무시 여부 (스케줄러에서는 True)

        Returns:
            TradingSignal: 생성된 신호 (DB에 저장됨)

        Raises:
            SignalServiceError: 신호 생성 실패 시
        """
        # 쿨다운 체크 (수동 호출 시)
        if not force:
            await self._check_cooldown()

        # 1. 시장 데이터 수집 및 샘플링
        raw_market_data = await self._get_recent_market_data()
        if not raw_market_data:
            raise SignalServiceError("분석할 시장 데이터가 없습니다")

        # 샘플링 적용 (토큰 절감)
        sampled_data = self._sampler.get_sampled_data(raw_market_data)
        sampling_stats = self._sampler.get_statistics(sampled_data)
        logger.info(
            f"시장 데이터 샘플링: {len(raw_market_data)}개 → {sampling_stats['total']}개 "
            f"(장기: {sampling_stats['long_term']}, 중기: {sampling_stats['mid_term']}, "
            f"단기: {sampling_stats['short_term']})"
        )

        # 최신 데이터는 raw에서 가져옴 (샘플링 전)
        latest_data = raw_market_data[0]
        current_price = float(latest_data.price)

        # 2. 멀티 타임프레임 분석
        try:
            mtf_result = await self.mtf_analyzer.analyze(self.ticker)
        except Exception as e:
            logger.warning(f"멀티 타임프레임 분석 실패: {e}")
            mtf_result = MultiTimeframeResult()

        # 3. 잔고 정보 조회
        balance_info = await self._get_balance_info()

        # 4. 프롬프트 생성 (코인 유형별 템플릿 사용, 샘플링된 데이터 사용)
        system_instruction = get_system_instruction(
            self.currency, self.coin_type, self.prompt_config
        )
        prompt = self._prompt_builder.build_enhanced_prompt(
            sampled_data=sampled_data,
            mtf_result=mtf_result,
            balance_info=balance_info,
        )

        # 디버그: 생성된 프롬프트 로깅 (민감 정보 마스킹)
        logger.info(f"AI 프롬프트 생성 완료 (길이: {len(prompt)}자)")
        logger.debug(f"프롬프트:\n{mask_sensitive_data(prompt)}")

        # 5. AI 호출
        ai_start_time = time.monotonic()
        try:
            response = await self.ai_client.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=0.3,
                max_output_tokens=1024,
            )
        except AIClientError as e:
            logger.error(f"AI 신호 생성 실패: {e}")
            raise SignalServiceError(f"AI API 오류: {e}") from e

        ai_elapsed_time = time.monotonic() - ai_start_time

        # 토큰 사용량 및 응답 시간 로깅
        logger.info(
            f"AI 호출 완료: 입력 {response.input_tokens}토큰, "
            f"출력 {response.output_tokens}토큰, "
            f"총 {response.input_tokens + response.output_tokens}토큰, "
            f"응답시간 {ai_elapsed_time:.2f}초"
        )

        # 토큰 목표 검증 (4,000 이하)
        if response.input_tokens > 4000:
            logger.warning(
                f"입력 토큰이 목표(4,000)를 초과했습니다: {response.input_tokens}"
            )

        # 6. 응답 파싱
        parsed = self._response_parser.parse_response(
            response.text,
            balance_info=balance_info,
        )

        # 7. 기술적 지표 스냅샷 생성
        technical_snapshot = self._prompt_builder.create_technical_snapshot(mtf_result)

        # 8. DB에 저장 (Repository 사용)
        signal = TradingSignal(
            market_data_id=latest_data.id,
            signal_type=parsed.signal_type,
            confidence=Decimal(str(parsed.confidence)),
            reasoning=parsed.reasoning,
            created_at=datetime.now(UTC),
            model_name=response.model_name,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            price_at_signal=Decimal(str(current_price)),
            technical_snapshot=technical_snapshot,
            user_id=user_id,
        )
        await self._signal_repo.save(signal)
        await self.db.commit()
        await self.db.refresh(signal)

        logger.info(
            f"신호 생성 완료: {parsed.signal_type} (신뢰도: {parsed.confidence:.2f}, "
            f"합류점수: {mtf_result.confluence_score:.2f})"
        )

        return signal

    async def _check_cooldown(self) -> None:
        """쿨다운 체크 (Repository 사용)"""
        cooldown_threshold = datetime.now(UTC) - timedelta(
            minutes=SIGNAL_COOLDOWN_MINUTES
        )

        recent_signals = await self._signal_repo.get_by_date_range(cooldown_threshold)
        if recent_signals:
            raise SignalServiceError(
                f"신호 생성 쿨다운 중입니다. {SIGNAL_COOLDOWN_MINUTES}분 후에 다시 시도하세요."
            )

    async def _get_recent_market_data(
        self,
        hours: int = SIGNAL_MARKET_DATA_HOURS,
    ) -> list[MarketData]:
        """최근 시장 데이터 조회"""
        since = datetime.now(UTC) - timedelta(hours=hours)

        stmt = (
            select(MarketData)
            .where(MarketData.timestamp > since)
            .order_by(desc(MarketData.timestamp))
            .limit(1000)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_balance_info(self) -> dict | None:
        """
        Upbit 잔고 정보 조회 (동적 코인 지원)

        Returns:
            dict | None: 잔고 정보 딕셔너리 또는 None (조회 실패 시)
        """
        try:
            private_api = get_upbit_private_api()
            accounts = await private_api.get_accounts()

            krw_available = Decimal("0")
            coin_available = Decimal("0")
            coin_avg_price = Decimal("0")

            for acc in accounts:
                if acc.currency == "KRW":
                    krw_available = acc.balance
                elif acc.currency == self.currency:
                    coin_available = acc.balance
                    coin_avg_price = acc.avg_buy_price

            # 현재가 조회 (mtf_analyzer의 public API 사용)
            try:
                ticker = await self.mtf_analyzer.upbit_client.get_ticker(self.ticker)
                current_price = ticker.trade_price
            except UpbitPublicAPIError:
                current_price = coin_avg_price

            # 미실현 손익 계산
            coin_value = coin_available * current_price
            total_krw = krw_available + coin_value
            unrealized_pnl = Decimal("0")
            unrealized_pnl_pct = 0.0

            if coin_available > 0 and coin_avg_price > 0:
                unrealized_pnl = (current_price - coin_avg_price) * coin_available
                unrealized_pnl_pct = float(
                    (current_price - coin_avg_price) / coin_avg_price * 100
                )

            return {
                "krw_available": krw_available,
                "coin_available": coin_available,
                "coin_avg_price": coin_avg_price,
                "current_price": current_price,
                "total_krw": total_krw,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": unrealized_pnl_pct,
            }

        except UpbitPrivateAPIError as e:
            logger.warning(f"잔고 조회 실패: {e.message}")
            return None
        except Exception as e:
            logger.warning(f"잔고 조회 중 오류: {e}")
            return None

    async def get_latest_signal(self) -> TradingSignal | None:
        """최신 신호 조회 (Repository 사용)"""
        return await self._signal_repo.get_latest_one()

    async def get_signals(
        self,
        limit: int = 50,
        offset: int = 0,
        signal_type: str | None = None,
    ) -> list[TradingSignal]:
        """신호 목록 조회 (Repository 사용)"""
        if signal_type and signal_type != "all":
            signal_type_enum = SignalType(signal_type.upper())
            return await self._signal_repo.get_by_type(signal_type_enum, limit=limit)

        signals = await self._signal_repo.get_latest(limit=limit + offset)
        return signals[offset : offset + limit]

    async def get_signals_count(self, signal_type: str | None = None) -> int:
        """신호 총 개수 조회"""
        stmt = select(func.count()).select_from(TradingSignal)

        if signal_type and signal_type != "all":
            stmt = stmt.where(TradingSignal.signal_type == signal_type.upper())

        result = await self.db.execute(stmt)
        return result.scalar() or 0


# === 싱글톤 팩토리 ===
def get_signal_service(db: AsyncSession) -> SignalService:
    """SignalService 인스턴스 생성"""
    return SignalService(db)
