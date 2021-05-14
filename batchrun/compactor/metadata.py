from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Tuple

from dateutil.parser import parse as parse_datetime

from ..enums import LogEntryKind

MICROSECOND = timedelta(microseconds=1)

DataDict = Dict[str, Any]


class LogEntryMetadataItem(NamedTuple):
    time: datetime
    kind: LogEntryKind
    length: int


class LogEntryMetadata:
    @classmethod
    def deserialize(cls, data: DataDict) -> "LogEntryMetadata":
        result = cls()
        version = data.get("v")
        if version == 1:
            result._load_from_v1_data(data)
        else:
            raise ValueError(f"Unsupported version: {version!r}")
        return result

    def __init__(self) -> None:
        self._items: List[LogEntryMetadataItem] = []

    @property
    def first_timestamp(self) -> Optional[datetime]:
        return self._items[0].time if self._items else None

    @property
    def last_timestamp(self) -> Optional[datetime]:
        return self._items[-1].time if self._items else None

    @property
    def entry_count(self) -> int:
        return len(self._items)

    @property
    def error_count(self) -> int:
        return sum(1 for x in self._items if x.kind == LogEntryKind.STDERR)

    def append_item(self, time: datetime, kind: LogEntryKind, length: int) -> None:
        self._items.append(LogEntryMetadataItem(time, kind, length))

    def items(self) -> Iterable[LogEntryMetadataItem]:
        return iter(self._items)

    def serialize(self, time_precision: timedelta = MICROSECOND) -> DataDict:
        entry_data = self._get_entry_data(time_precision)
        start = self.first_timestamp
        data = {
            "v": 1,
            "p": int(time_precision / MICROSECOND),
            "s": start.isoformat() if start else "",
            "d": entry_data,
        }
        return data

    def _load_from_v1_data(self, data: Dict[str, Any]) -> None:
        precision_us = data.get("p")
        if not isinstance(precision_us, int):
            raise ValueError(f"Invalid precision: {precision_us!r}")

        start = data.get("s")
        if not isinstance(start, str):
            raise ValueError(f"Invalid start timestamp: {start!r}")

        entry_data = data.get("d")
        if not isinstance(entry_data, list):
            raise ValueError(f"Invalid data type: {type(entry_data).__name__}")
        if len(entry_data) != 3:
            raise ValueError(f"Data length mismatch: {len(entry_data)}")

        first_timestamp = parse_datetime(start) if start else None
        time_precision = precision_us * MICROSECOND

        if first_timestamp is None:
            assert entry_data == [[], [], []]
            return

        total_time = 0
        for (delta, kind_value, length) in zip(*entry_data):
            total_time += delta
            total_delta = total_time * time_precision
            time = first_timestamp + total_delta
            kind = LogEntryKind(kind_value)
            self.append_item(time, kind, length)

    def _get_entry_data(
        self, time_precision: timedelta = MICROSECOND,
    ) -> Tuple[List[int], List[int], List[int]]:
        ts0: Optional[datetime] = None
        total_delta_so_far: int = 0

        time_deltas: List[int] = []
        kinds: List[int] = []
        lengths: List[int] = []

        for (ts, kind, length) in self._items:
            if ts0 is None:
                ts0 = ts
            delta = int((ts - ts0) / time_precision) - total_delta_so_far
            total_delta_so_far += delta

            time_deltas.append(delta)
            kinds.append(kind.value)
            lengths.append(length)

        return (time_deltas, kinds, lengths)
