TITLE_MAX_LENGTH = 100
CONTENT_MAX_LENGTH = 5000

SOLUTION_REQUIRED = "해결 상태로 바꾸려면 해결 방법을 입력해 주세요."


def text_error(value: str | None, label: str, max_length: int) -> str | None:
    """1자 이상 max_length자 이하인지 확인합니다. 공백만 있으면 빈 입력으로 봅니다."""
    message = f"{label}은 1~{max_length:,}자로 입력해 주세요."
    if value is None or not value.strip():
        return message
    if len(value) > max_length:
        return message
    return None
