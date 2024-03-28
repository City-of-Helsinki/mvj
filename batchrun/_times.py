import time
from datetime import datetime, timezone
from typing import NewType

AwareDateTime = NewType("AwareDateTime", datetime)


def check_is_aware(dt: datetime) -> AwareDateTime:
    if not dt.tzinfo:
        raise ValueError("Given datetime is missing timezone information")
    return AwareDateTime(dt)


def utc_now() -> AwareDateTime:
    return datetime.fromtimestamp(time.time(), timezone.utc)  # type: ignore


class TZAwareDateTime(datetime):
    """A datetime subclass that includes timezone offset information in equality checks."""

    def __eq__(self, other):
        if not isinstance(other, TZAwareDateTime):
            return NotImplemented
        return super().__eq__(other) and self.utcoffset() == other.utcoffset()

    def __hash__(self):
        return hash((super().__hash__(), self.utcoffset()))
