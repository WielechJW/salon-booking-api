from datetime import datetime, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo

from app.config import get_settings

UTC = timezone.utc


@lru_cache
def get_salon_timezone() -> ZoneInfo:
    return ZoneInfo(get_settings().salon_timezone)


def as_utc(value: datetime) -> datetime:
    """Return a database datetime as an aware UTC datetime.

    PostgreSQL returns aware values. SQLite drops timezone information, but
    stores the already-normalized UTC wall time, so naive values are UTC here.
    """
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def utc_now() -> datetime:
    return datetime.now(UTC)
