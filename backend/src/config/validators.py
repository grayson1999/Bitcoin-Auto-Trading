"""
설정값 검증 모듈

DB 오버라이드 설정 쓰기 시, Settings 필드에 선언된 타입·범위(ge/le) 제약을
재사용해 값을 검증한다. 환경변수 로드 시에만 적용되던 Pydantic 제약이
DB 오버라이드 경로에서도 동일하게 적용되도록 하는 단일 진실원.
"""

from typing import Any

import annotated_types as at

from src.config.settings import Settings


def validate_config_value(key: str, value: Any) -> Any:
    """
    설정값을 Settings 필드의 타입·범위 제약으로 검증한다.

    Args:
        key: 설정 키 (Settings의 필드명)
        value: 검증할 값

    Returns:
        Any: 검증·정규화된 값 (float 필드는 float로 변환)

    Raises:
        ValueError: 알 수 없는 키, 타입 불일치, 범위 초과 시
    """
    field = Settings.model_fields.get(key)
    if field is None:
        raise ValueError(f"'{key}'는 알 수 없는 설정 키입니다")

    annotation = field.annotation

    # bool은 int의 서브클래스이므로 먼저 검사
    if annotation is bool:
        if not isinstance(value, bool):
            raise ValueError(f"'{key}'는 불리언(true/false)이어야 합니다")
        return value

    if annotation is int:
        # bool은 int지만 허용하지 않음
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"'{key}'는 정수여야 합니다 (입력: {value!r})")
    elif annotation is float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"'{key}'는 숫자여야 합니다 (입력: {value!r})")
        value = float(value)
    elif annotation is str:
        if not isinstance(value, str):
            raise ValueError(f"'{key}'는 문자열이어야 합니다 (입력: {value!r})")
        return value

    # 숫자 범위(ge/le) 검증
    for meta in field.metadata:
        if isinstance(meta, at.Ge) and value < meta.ge:
            raise ValueError(f"'{key}'는 {meta.ge} 이상이어야 합니다 (입력: {value})")
        if isinstance(meta, at.Le) and value > meta.le:
            raise ValueError(f"'{key}'는 {meta.le} 이하여야 합니다 (입력: {value})")

    return value
