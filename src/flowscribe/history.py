"""Session history with undo and export.

New in v0.2. Every dictation in a session is kept locally so a bad
paste is never the end of the story: undo walks back, and the whole
session exports to clean Markdown, which doubles as a writing log.
Stored as plain JSON when saved, on the user's disk only.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Entry:
    raw: str
    text: str
    timestamp: float = field(default_factory=time.time)


class History:
    def __init__(self):
        self.entries: list[Entry] = []

    def add(self, raw: str, text: str) -> Entry:
        entry = Entry(raw=raw, text=text)
        self.entries.append(entry)
        return entry

    def undo(self) -> Entry | None:
        """Remove and return the most recent entry, or None."""
        if not self.entries:
            return None
        return self.entries.pop()

    def last(self) -> Entry | None:
        return self.entries[-1] if self.entries else None

    def export_markdown(self) -> str:
        lines = ["# FlowScribe Session", ""]
        for entry in self.entries:
            stamp = time.strftime("%H:%M:%S",
                                  time.localtime(entry.timestamp))
            lines.append(f"- `{stamp}` {entry.text}")
        return "\n".join(lines) + "\n"

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(
            [asdict(e) for e in self.entries], indent=2))

    @classmethod
    def load(cls, path: str | Path) -> "History":
        history = cls()
        for row in json.loads(Path(path).read_text()):
            history.entries.append(Entry(**row))
        return history
