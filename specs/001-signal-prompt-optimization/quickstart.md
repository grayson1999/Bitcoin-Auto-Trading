# Quickstart: AI 신호 프롬프트 최적화

**Branch**: `001-signal-prompt-optimization`
**Date**: 2026-01-24

---

## 개요

이 기능은 AI 매매 신호 생성 시스템을 최적화합니다:
- 신호 주기: 1시간 → 30분
- 토큰 사용: 10,000 → 4,000 (60% 절감)
- 비용: 동일 예산으로 2배 빈번한 신호

---

## 테스트 방법

### 1. 샘플링 로직 테스트

```bash
cd backend
pytest tests/unit/signal/test_sampler.py -v
```

### 2. 신호 생성 통합 테스트

```bash
# 개발 서버 실행
make dev-backend

# 수동 신호 생성 (API 호출)
curl -X POST http://localhost:8000/api/v1/signals/generate \
  -H "Authorization: Bearer $TOKEN"
```

### 3. 토큰 사용량 확인

```bash
# 로그에서 토큰 사용량 확인
journalctl -u bitcoin-backend | grep "input_tokens"
```

---

## 설정 변경

### 신호 주기 변경 (DB 오버라이드)

```bash
# PostgreSQL 접속
PGPASSWORD=trading psql -h localhost -U trading -d trading

# 30분 → 15분으로 변경 (필요 시)
INSERT INTO system_config (config_key, config_value)
VALUES ('signal_interval_minutes', '15')
ON CONFLICT (config_key) DO UPDATE SET config_value = '15';
```

### 환경변수 (기본값)

```bash
# .env (변경 없음)
# signal_interval_minutes는 DB 오버라이드로 관리
```

---

## 검증 체크리스트

- [ ] 30분마다 신호 생성 확인
- [ ] 입력 토큰 4,000개 이하 확인
- [ ] AI 응답 시간 2-4초 확인
- [ ] 신뢰도 0.5 고정 출력 비율 감소 확인
- [ ] 대시보드에서 성과 데이터 정상 표시 확인

---

## 롤백

문제 발생 시 develop 브랜치로 복귀:

```bash
git checkout develop
sudo systemctl restart bitcoin-backend
```

---

## 관련 파일

| 파일 | 변경 내용 |
|------|----------|
| `config/settings.py` | signal_interval_minutes 추가 |
| `config/constants.py` | SAMPLING_CONFIG 추가 |
| `scheduler/scheduler.py` | IntervalTrigger(minutes=) |
| `modules/signal/sampler.py` | [NEW] 샘플링 모듈 |
| `modules/signal/service.py` | 샘플링 적용, 성과 피드백 제거 |
| `modules/signal/prompt/builder.py` | performance_feedback 제거 |
| `modules/signal/prompt/templates.py` | 프롬프트 압축 |
