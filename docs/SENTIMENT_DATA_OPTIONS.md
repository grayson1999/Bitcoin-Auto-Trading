# 감성 데이터 통합 옵션

비트코인 자동 거래 시스템에 비정형(감성) 데이터를 추가하기 위한 옵션 분석 문서입니다.

---

## 현재 시스템 분석

### 이미 구현된 데이터

| 카테고리 | 구현 상태 | 파일 위치 |
|----------|-----------|-----------|
| 기술적 지표 (RSI, MACD, BB, EMA, ATR) | ✅ 완료 | `modules/market/analysis/indicators.py` |
| 멀티 타임프레임 분석 (1H, 4H, 1D, 1W) | ✅ 완료 | `modules/market/analysis/multi_timeframe.py` |
| 성과 피드백 (과거 신호 정확도) | ✅ 완료 | `modules/signal/tracker/performance_tracker.py` |
| **Fear & Greed Index (BTC 기반)** | ✅ 완료 | `clients/sentiment/fear_greed.py` |

### 현재 AI 프롬프트 구조

```
1. 포지션 상태 (잔고, 평균매수가, 미실현손익)
2. 리스크 체크 (손절 조건)
3. 기술적 지표 (RSI, MACD, BB, EMA, ATR)
4. 멀티 타임프레임 분석 (추세, 강도, 합류점수)
5. 시장 심리 지표 (BTC Fear & Greed Index) ← 신규 추가
6. 성과 피드백 (과거 신호 정확도)
```

---

## Fear & Greed Index (구현 완료)

### 개요
- **제공**: Alternative.me
- **API 엔드포인트**: `https://api.alternative.me/fng/`
- **비용**: 완전 무료, Rate Limit 없음
- **업데이트 주기**: 하루 1회 (UTC 00:00)

### 중요: BTC 기반 지표

**Fear & Greed Index는 BTC(비트코인) 시장 심리를 측정합니다.**

직접 거래하는 코인의 지표가 아니므로, 코인 유형별로 다르게 활용해야 합니다.

### 코인 유형별 활용 전략

| 코인 유형 | BTC 상관관계 | 지표 활용도 | 활용 방법 |
|----------|-------------|------------|----------|
| **메이저** (BTC, ETH 등) | 높음 | 적극 활용 | 역발상 매수/익절 검토 |
| **알트코인** (분류 외) | 중간 | 참고용 | 기술적 지표 우선, 배경 정보로 활용 |
| **밈코인** (DOGE, SHIB 등) | 낮음 | 배경 정보 | 거래량/모멘텀 우선, 참고만 |

### 지표 해석 및 활용

| 값 범위 | 분류 | 시장 심리 | 메이저 코인 | 알트/밈코인 |
|---------|------|----------|------------|------------|
| 0-24 | Extreme Fear | 극도의 공포 | 역발상 매수 적극 검토 | 참고만 |
| 25-49 | Fear | 공포 | 신중한 매수 기회 탐색 | 참고만 |
| 50 | Neutral | 중립 | 기술적 지표 우선 | 기술적 지표 우선 |
| 51-74 | Greed | 탐욕 | 익절 검토, 신규 매수 주의 | 참고만 |
| 75-100 | Extreme Greed | 극도의 탐욕 | 과열 경고, 분할 익절 권장 | 참고만 |

### 구현 파일

| 파일 | 역할 |
|------|------|
| `clients/sentiment/fear_greed.py` | API 클라이언트 |
| `clients/sentiment/__init__.py` | 패키지 초기화 |
| `modules/signal/prompt/builder.py` | 프롬프트 포맷 (`_format_sentiment`) |
| `modules/signal/prompt/templates.py` | 코인 유형별 활용 가이드 |
| `modules/signal/service.py` | 신호 생성 시 통합 |

### 프롬프트 출력 예시

**극도의 공포 구간 (메이저 코인):**
```
### 시장 심리 지표 (BTC 기준)
- Fear & Greed Index: 18/100 (극도의 공포)
- 측정 시각: 2026-01-29 00:00 UTC

**[BTC 시장 극도의 공포 구간]**
- 메이저 코인은 BTC와 상관관계 높음
- 역발상 매수 기회 적극 검토 (기술적 바닥 확인 필수)
```

**극도의 탐욕 구간 (밈코인):**
```
### 시장 심리 지표 (BTC 기준)
- Fear & Greed Index: 82/100 (극도의 탐욕)
- 측정 시각: 2026-01-29 00:00 UTC

**[BTC 시장 극도의 탐욕 구간]**
- 밈코인은 BTC와 상관관계 낮음
- 배경 정보로만 참고, 거래량/모멘텀 우선
```

---

## 옵션 비교 요약

| 옵션 | 비용 | 실시간성 | 구현 복잡도 | 상태 |
|------|------|----------|-------------|------|
| **Fear & Greed Index** | **무료** | 하루 1회 | ⭐ Low | ✅ 구현 완료 |
| Crypto News Headlines | 무료/유료 | 실시간 | ⭐⭐ Medium | 미구현 |
| Social Media Sentiment | 유료 | 실시간 | ⭐⭐⭐ High | 미구현 |

---

## 옵션 2: Crypto News Headlines (미구현)

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

### 구현 시기
- Fear & Greed Index 효과 검증 후 ROI 판단

---

## 옵션 3: Social Media Sentiment (미구현)

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

### 구현 시기
- Fear & Greed Index + CryptoPanic 효과 검증 후 장기 과제로 검토

---

## 참고 자료

- [Alternative.me Fear & Greed API](https://alternative.me/crypto/fear-and-greed-index/)
- [CryptoPanic API Docs](https://cryptopanic.com/developers/api/)
- [Twitter API v2](https://developer.twitter.com/en/docs/twitter-api)
- [Reddit API](https://www.reddit.com/dev/api/)

---

## 작성 정보
- 최초 작성일: 2026-01-29
- 최종 수정일: 2026-01-29
- 목적: 감성 데이터 통합 옵션 분석 및 구현 가이드
- 현재 상태: **Fear & Greed Index 구현 완료** (BTC 기반, 코인 유형별 활용 가이드 포함)
