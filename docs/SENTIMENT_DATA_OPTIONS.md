# 감성 데이터 통합 옵션

비트코인 자동 거래 시스템에 비정형(감성) 데이터를 추가하기 위한 옵션 분석 문서입니다.

---

## 옵션 비교 요약

| 옵션 | 비용 | 실시간성 | 구현 복잡도 | 권장 우선순위 |
|------|------|----------|-------------|---------------|
| Fear & Greed Index | 무료 | 하루 1회 | ⭐ Low | 1위 (권장) |
| Crypto News Headlines | 무료/유료 | 실시간 | ⭐⭐ Medium | 2위 |
| Social Media Sentiment | 유료 | 실시간 | ⭐⭐⭐ High | 3위 |

---

## 옵션 1: Fear & Greed Index (권장)

### 개요
- **제공**: Alternative.me
- **API 엔드포인트**: `https://api.alternative.me/fng/`
- **비용**: 완전 무료, Rate Limit 없음
- **업데이트 주기**: 하루 1회 (UTC 00:00)

### 장점
- 완전 무료, API 키 불필요
- 간단한 구현 (단일 GET 요청)
- 비트코인 시장 심리 종합 지표 (변동성, 거래량, SNS, 설문 등 종합)
- 0-100 스케일로 해석 용이

### 단점
- 하루 1회 업데이트로 실시간성 부족
- 비트코인 전용 (알트코인 별도 지표 없음)

### API 응답 예시
```json
{
  "name": "Fear and Greed Index",
  "data": [
    {
      "value": "24",
      "value_classification": "Extreme Fear",
      "timestamp": "1706400000",
      "time_until_update": "86400"
    }
  ]
}
```

### 지표 해석
| 값 범위 | 분류 | 시장 심리 |
|---------|------|----------|
| 0-24 | Extreme Fear | 극도의 공포 → 매수 기회? |
| 25-49 | Fear | 공포 |
| 50 | Neutral | 중립 |
| 51-74 | Greed | 탐욕 |
| 75-100 | Extreme Greed | 극도의 탐욕 → 매도 기회? |

### 구현 예시

```python
# backend/src/clients/sentiment/fear_greed.py

import httpx
from dataclasses import dataclass
from datetime import datetime

@dataclass
class FearGreedData:
    value: int
    classification: str
    timestamp: datetime

class FearGreedClient:
    API_URL = "https://api.alternative.me/fng/"

    async def get_current(self) -> FearGreedData:
        async with httpx.AsyncClient() as client:
            response = await client.get(self.API_URL)
            data = response.json()["data"][0]
            return FearGreedData(
                value=int(data["value"]),
                classification=data["value_classification"],
                timestamp=datetime.fromtimestamp(int(data["timestamp"]))
            )
```

### AI 프롬프트 통합 예시

```python
# builder.py에 추가

def _format_sentiment(self, fear_greed: FearGreedData) -> str:
    lines = [
        "### 시장 심리 지표",
        f"- Fear & Greed Index: {fear_greed.value}/100 ({fear_greed.classification})",
    ]

    if fear_greed.value <= 24:
        lines.append("- ⚠️ 극도의 공포 구간: 역발상 매수 검토 가능")
    elif fear_greed.value >= 75:
        lines.append("- ⚠️ 극도의 탐욕 구간: 과열 주의, 익절 검토")

    return "\n".join(lines)
```

---

## 옵션 2: Crypto News Headlines

### 개요
- **제공**: CryptoPanic API
- **웹사이트**: https://cryptopanic.com/developers/api/
- **비용**: 무료 (1시간 500건), 유료 플랜 가능
- **기능**: 암호화폐 뉴스 헤드라인 + 감성 분류

### 장점
- 실시간 뉴스 이벤트 감지
- API가 자체 감성 분류 제공 (positive/negative/neutral)
- 특정 코인별 필터링 가능

### 단점
- API 키 필요 (무료 등록)
- Rate Limit 존재 (1시간 500건)
- 영어 뉴스 중심

### API 응답 예시
```json
{
  "results": [
    {
      "title": "Bitcoin Surges Past $100K as Institutional Demand Grows",
      "published_at": "2024-01-15T10:30:00Z",
      "votes": { "positive": 45, "negative": 5 },
      "sentiment": "positive"
    }
  ]
}
```

### 구현 복잡도
- API 키 관리 필요
- 감성 집계 로직 구현 (최근 N시간 뉴스 평균)
- 캐싱 필요 (Rate Limit 대응)

---

## 옵션 3: Social Media Sentiment

### 개요
- **제공**: Twitter/X API, Reddit API
- **비용**: Twitter API는 유료 ($100+/월), Reddit API는 무료/유료
- **기능**: 실시간 트윗/게시물 감성 분석

### 장점
- 가장 높은 실시간성
- 커뮤니티 반응 직접 측정
- 다양한 코인별 분석 가능

### 단점
- Twitter API 유료화 ($100+/월 기본 플랜)
- 자체 NLP 감성 분석 필요 (또는 외부 API 추가 비용)
- 노이즈 많음 (봇, 스팸 필터링 필요)
- 구현 복잡도 높음

### 구현 요구사항
1. Twitter/Reddit API 인증
2. NLP 감성 분석 모델 (VADER, BERT 등)
3. 봇/스팸 필터링 로직
4. 데이터 정규화 및 집계

---

## 구현 권장 순서

### 1단계: Fear & Greed Index (즉시 구현 가능)
- 구현 시간: 1-2시간
- 효과: 시장 전반 심리 반영
- 리스크: 낮음

### 2단계: CryptoPanic News (선택적)
- 구현 시간: 4-6시간
- 효과: 실시간 이벤트 반응
- 리스크: 중간 (Rate Limit 관리 필요)

### 3단계: Social Media (장기 과제)
- 구현 시간: 2-3일
- 효과: 최신 커뮤니티 반응
- 리스크: 높음 (비용, 복잡도)

---

## 참고 자료

- [Alternative.me Fear & Greed API](https://alternative.me/crypto/fear-and-greed-index/)
- [CryptoPanic API Docs](https://cryptopanic.com/developers/api/)
- [Twitter API v2](https://developer.twitter.com/en/docs/twitter-api)
- [Reddit API](https://www.reddit.com/dev/api/)

---

## 작성 정보
- 작성일: 2026-01-29
- 목적: 감성 데이터 통합 옵션 분석 및 구현 가이드
