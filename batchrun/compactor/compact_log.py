from dataclasses import dataclass
from datetime import datetime
from io import StringIO
from typing import Any, Dict, Iterable, Optional, Protocol

from ..enums import LogEntryKind
from .metadata import LogEntryMetadata


class LogEntry(Protocol):
    @property
    def time(self) -> datetime:
        pass

    @property
    def kind(self) -> LogEntryKind:
        pass

    @property
    def text(self) -> str:
        pass


@dataclass(frozen=True)
class LogEntryDatum:
    time: datetime
    kind: LogEntryKind
    text: str


@dataclass(frozen=True)
class CompactLog:
    content: str
    entry_data: Dict[str, Any]
    first_timestamp: Optional[datetime]
    last_timestamp: Optional[datetime]
    entry_count: int
    error_count: int

    @classmethod
    def from_log_entries(cls, entries: Iterable[LogEntry]) -> "CompactLog":
        message_stream = StringIO()
        metadata = LogEntryMetadata()
        for entry in entries:
            text = entry.text
            message_stream.write(text)
            metadata.append_item(entry.time, entry.kind, len(text))

        return cls(
            content=message_stream.getvalue(),
            entry_data=metadata.serialize(),
            first_timestamp=metadata.first_timestamp,
            last_timestamp=metadata.last_timestamp,
            entry_count=metadata.entry_count,
            error_count=metadata.error_count,
        )

    def iterate_entries(self) -> Iterable[LogEntryDatum]:
        metadata = self.get_metadata()
        position = 0
        for time, kind, length in metadata.items():
            text = self.content[position : (position + length)]
            position += length
            yield LogEntryDatum(time, kind, text)

    def get_metadata(self) -> LogEntryMetadata:
        return LogEntryMetadata.deserialize(self.entry_data)
