"""
설정값 검증 (H6) 단위 테스트

validate_config_value가 Settings Field의 타입·범위 제약을 재사용해
DB 오버라이드 쓰기 경로에서도 범위/타입을 강제하는지 검증한다.
"""

import pytest

from src.config.validators import validate_config_value

# === 범위 검증 (float) ===


def test_stop_loss_over_max_raises() -> None:
    """stop_loss_pct=999 → le=10 초과로 ValueError."""
    with pytest.raises(ValueError, match="10"):
        validate_config_value("stop_loss_pct", 999)


def test_stop_loss_below_min_raises() -> None:
    """stop_loss_pct=0.1 → ge=1.5 미만으로 ValueError."""
    with pytest.raises(ValueError, match=r"1\.5"):
        validate_config_value("stop_loss_pct", 0.1)


def test_stop_loss_in_range_ok() -> None:
    """stop_loss_pct=5.0 → 통과, float 반환."""
    assert validate_config_value("stop_loss_pct", 5.0) == 5.0


def test_position_size_max_over_limit_raises() -> None:
    """position_size_max_pct=200 → le=100 초과."""
    with pytest.raises(ValueError):
        validate_config_value("position_size_max_pct", 200)


# === 타입 검증 ===


def test_int_field_rejects_float() -> None:
    """signal_interval_minutes=10.5 → 정수 아님."""
    with pytest.raises(ValueError, match="정수"):
        validate_config_value("signal_interval_minutes", 10.5)


def test_int_field_accepts_int() -> None:
    """signal_interval_minutes=60 → 통과."""
    assert validate_config_value("signal_interval_minutes", 60) == 60


def test_bool_field_rejects_string() -> None:
    """profit_take_enabled='yes' → 불리언 아님."""
    with pytest.raises(ValueError, match="불리언"):
        validate_config_value("profit_take_enabled", "yes")


def test_bool_field_accepts_bool() -> None:
    """profit_take_enabled=True → 통과."""
    assert validate_config_value("profit_take_enabled", True) is True


def test_str_field_rejects_number() -> None:
    """ai_model=123 → 문자열 아님."""
    with pytest.raises(ValueError, match="문자열"):
        validate_config_value("ai_model", 123)


def test_str_field_accepts_str() -> None:
    """ai_model='gpt-5-nano' → 통과."""
    assert validate_config_value("ai_model", "gpt-5-nano") == "gpt-5-nano"


def test_float_field_rejects_bool() -> None:
    """float 필드에 bool 주입 차단 (bool은 int 서브클래스)."""
    with pytest.raises(ValueError):
        validate_config_value("stop_loss_pct", True)


# === 알 수 없는 키 ===


def test_unknown_key_raises() -> None:
    """존재하지 않는 키 → ValueError."""
    with pytest.raises(ValueError, match="알 수 없는"):
        validate_config_value("nonexistent_key", 5)
