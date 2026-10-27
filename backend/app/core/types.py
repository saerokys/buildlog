from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator


def utc_now() -> datetime:
    return datetime.now(UTC)


class UTCDateTime(TypeDecorator):
    """날짜·시간을 항상 UTC로 저장하고, 읽을 때도 UTC 시간대가 붙은 값으로 돌려줍니다.

    SQLite는 시간대 정보를 저장하지 못하고 PostgreSQL은 저장하므로,
    두 데이터베이스에서 같은 값을 얻도록 여기서 맞춥니다.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("시간대 정보가 없는 날짜·시간은 저장할 수 없습니다.")
        value = value.astimezone(UTC)
        if dialect.name == "sqlite":
            return value.replace(tzinfo=None)
        return value

    def process_result_value(self, value: datetime | None, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
