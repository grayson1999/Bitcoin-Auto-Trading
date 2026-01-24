"""
민감 정보 마스킹 유틸리티 테스트

mask_sensitive_data 함수가 다양한 민감 정보를 올바르게 마스킹하는지 검증합니다.

테스트 대상:
- API 키 마스킹 (Upbit, Gemini, OpenAI)
- 토큰 마스킹 (Bearer, JWT)
- 잔고 정보 마스킹 (JSON 형식)
- 혼합 패턴 마스킹
- 비민감 정보 보존
"""

import pytest

from src.config.logging import mask_sensitive_data


class TestMaskSensitiveData:
    """mask_sensitive_data 함수 테스트"""

    # === API 키 마스킹 테스트 ===

    def test_mask_upbit_access_key(self) -> None:
        """Upbit access key 마스킹"""
        message = 'upbit_access_key = "abc123xyz"'
        result = mask_sensitive_data(message)
        assert "abc123xyz" not in result
        assert "***" in result

    def test_mask_upbit_secret_key(self) -> None:
        """Upbit secret key 마스킹"""
        message = 'upbit_secret_key: "secret456"'
        result = mask_sensitive_data(message)
        assert "secret456" not in result
        assert "***" in result

    def test_mask_gemini_api_key(self) -> None:
        """Gemini API key 마스킹"""
        message = "gemini_api_key='AIzaSyB123abc'"
        result = mask_sensitive_data(message)
        assert "AIzaSyB123abc" not in result
        assert "***" in result

    def test_mask_openai_api_key(self) -> None:
        """OpenAI API key 마스킹"""
        message = "openai_api_key=sk-proj-abcdefghijklmnop"
        result = mask_sensitive_data(message)
        assert "sk-proj-abcdefghijklmnop" not in result
        assert "***" in result

    def test_mask_generic_api_key(self) -> None:
        """일반 API key 마스킹"""
        message = 'api_key: "test-api-key-12345"'
        result = mask_sensitive_data(message)
        assert "test-api-key-12345" not in result
        assert "***" in result

    def test_mask_slack_webhook_url(self) -> None:
        """Slack webhook URL 마스킹"""
        message = "slack_webhook_url=https://hooks.slack.com/services/T00/B00/xxx"
        result = mask_sensitive_data(message)
        assert "hooks.slack.com" not in result
        assert "***" in result

    # === 토큰 마스킹 테스트 ===

    def test_mask_bearer_token(self) -> None:
        """Bearer 토큰 마스킹"""
        message = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc123"
        result = mask_sensitive_data(message)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result
        assert "Bearer ***" in result

    def test_mask_jwt_token(self) -> None:
        """JWT 토큰 마스킹 (eyJ로 시작하는 3개 세그먼트)"""
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        message = f"Token: {jwt}"
        result = mask_sensitive_data(message)
        assert jwt not in result
        assert "***JWT***" in result

    # === 잔고 정보 마스킹 테스트 ===

    def test_mask_balance_json(self) -> None:
        """잔고 정보 마스킹 (JSON 형식)"""
        message = '{"balance": 1000000}'
        result = mask_sensitive_data(message)
        assert "1000000" not in result
        assert '"balance": "***"' in result

    def test_mask_krw_balance(self) -> None:
        """KRW 잔고 마스킹"""
        message = '{"krw": 500000.50}'
        result = mask_sensitive_data(message)
        assert "500000.50" not in result
        assert '"krw": "***"' in result

    def test_mask_btc_balance(self) -> None:
        """BTC 잔고 마스킹"""
        message = '{"btc": 0.12345678}'
        result = mask_sensitive_data(message)
        assert "0.12345678" not in result
        assert '"btc": "***"' in result

    def test_mask_coin_balance(self) -> None:
        """코인 잔고 마스킹"""
        message = '{"coin_balance": 100.5}'
        result = mask_sensitive_data(message)
        assert "100.5" not in result
        assert '"coin_balance": "***"' in result

    def test_mask_available_balance(self) -> None:
        """가용 잔고 마스킹"""
        message = '{"available": 999.99}'
        result = mask_sensitive_data(message)
        assert "999.99" not in result
        assert '"available": "***"' in result

    def test_mask_locked_balance(self) -> None:
        """잠긴 잔고 마스킹"""
        message = '{"locked": 100}'
        result = mask_sensitive_data(message)
        assert "100" not in result
        assert '"locked": "***"' in result

    # === 복합 패턴 테스트 ===

    def test_mask_multiple_sensitive_fields(self) -> None:
        """여러 민감 정보 동시 마스킹"""
        message = '{"balance": 1000, "krw": 500, "btc": 0.1}'
        result = mask_sensitive_data(message)
        assert "1000" not in result
        assert "500" not in result
        assert "0.1" not in result
        assert result.count('"***"') == 3

    def test_mask_api_key_and_balance(self) -> None:
        """API 키와 잔고 동시 마스킹"""
        message = 'api_key: "secret123", "balance": 1000000'
        result = mask_sensitive_data(message)
        assert "secret123" not in result
        assert "1000000" not in result
        assert "***" in result

    # === 비민감 정보 보존 테스트 ===

    def test_preserve_non_sensitive_data(self) -> None:
        """비민감 정보는 그대로 유지"""
        message = "시장 데이터: 가격=50000000, 거래량=100"
        result = mask_sensitive_data(message)
        assert result == message  # 변경 없음

    def test_preserve_partial_match(self) -> None:
        """부분 매치는 마스킹하지 않음"""
        message = "API 호출 완료, 총 balance_count: 5개"
        result = mask_sensitive_data(message)
        # balance_count는 JSON 형식의 balance가 아니므로 유지
        assert "balance_count: 5" in result

    def test_empty_string(self) -> None:
        """빈 문자열 처리"""
        result = mask_sensitive_data("")
        assert result == ""

    def test_no_sensitive_data(self) -> None:
        """민감 정보가 없는 경우"""
        message = "일반 로그 메시지입니다."
        result = mask_sensitive_data(message)
        assert result == message

    # === 대소문자 구분 테스트 ===

    def test_case_insensitive_api_key(self) -> None:
        """API 키 마스킹은 대소문자 구분 없음"""
        message_lower = 'upbit_access_key = "key123"'
        message_upper = 'UPBIT_ACCESS_KEY = "key123"'
        message_mixed = 'Upbit_Access_Key = "key123"'

        assert "key123" not in mask_sensitive_data(message_lower)
        assert "key123" not in mask_sensitive_data(message_upper)
        assert "key123" not in mask_sensitive_data(message_mixed)

    def test_case_insensitive_balance(self) -> None:
        """잔고 마스킹은 대소문자 구분 없음"""
        message_lower = '{"balance": 100}'
        message_upper = '{"BALANCE": 100}'
        message_mixed = '{"Balance": 100}'

        assert "100" not in mask_sensitive_data(message_lower)
        assert "100" not in mask_sensitive_data(message_upper)
        assert "100" not in mask_sensitive_data(message_mixed)


class TestMaskSensitiveDataEdgeCases:
    """마스킹 함수 엣지 케이스 테스트"""

    def test_nested_json_balance(self) -> None:
        """중첩된 JSON 구조의 잔고 마스킹"""
        message = '{"data": {"balance": 12345}}'
        result = mask_sensitive_data(message)
        assert "12345" not in result
        assert '"balance": "***"' in result

    def test_balance_with_comma_separator(self) -> None:
        """쉼표가 포함된 잔고 마스킹"""
        message = '{"balance": "1,000,000"}'
        result = mask_sensitive_data(message)
        assert "1,000,000" not in result

    def test_multiple_jwt_tokens(self) -> None:
        """여러 JWT 토큰 마스킹"""
        jwt1 = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abc"
        jwt2 = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIyIn0.xyz"
        message = f"Token1: {jwt1}, Token2: {jwt2}"
        result = mask_sensitive_data(message)
        assert jwt1 not in result
        assert jwt2 not in result
        assert result.count("***JWT***") == 2

    def test_long_api_key(self) -> None:
        """긴 API 키 마스킹"""
        long_key = "a" * 100
        message = f"api_key={long_key}"
        result = mask_sensitive_data(message)
        assert long_key not in result
        assert "***" in result

    def test_special_characters_in_key(self) -> None:
        """특수 문자가 포함된 API 키 마스킹"""
        message = 'api_key: "key-with_special.chars+123"'
        result = mask_sensitive_data(message)
        assert "key-with_special.chars+123" not in result
        assert "***" in result
