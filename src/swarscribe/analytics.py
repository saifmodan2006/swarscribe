"""Dictation analytics: prove the time dictation saves you.

SwarScribe tracks every session locally (never uploaded) and can
report words dictated, speaking speed, and estimated minutes saved
versus typing at an average 40 words per minute.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .storage import write_json

TYPING_WPM = 40.0


@dataclass
class Session:
    words: int
    seconds: float
    timestamp: float = field(default_factory=time.time)

    @property
    def wpm(self) -> float:
        if self.seconds <= 0:
            return 0.0
        return self.words / (self.seconds / 60.0)

    @property
    def minutes_saved(self) -> float:
        typing_minutes = self.words / TYPING_WPM
        dictation_minutes = self.seconds / 60.0
        return max(0.0, typing_minutes - dictation_minutes)


@dataclass
class Analytics:
    sessions: list[Session] = field(default_factory=list)

    def record(self, text: str, seconds: float) -> Session:
        session = Session(words=len(text.split()), seconds=seconds)
        self.sessions.append(session)
        return session

    @property
    def total_words(self) -> int:
        return sum(s.words for s in self.sessions)

    @property
    def total_minutes_saved(self) -> float:
        return sum(s.minutes_saved for s in self.sessions)

    @property
    def average_wpm(self) -> float:
        total_seconds = sum(s.seconds for s in self.sessions)
        if total_seconds <= 0:
            return 0.0
        return self.total_words / (total_seconds / 60.0)

    def summary(self) -> dict:
        return {
            "sessions": len(self.sessions),
            "total_words": self.total_words,
            "average_wpm": round(self.average_wpm, 1),
            "minutes_saved": round(self.total_minutes_saved, 1),
            "typing_wpm_baseline": TYPING_WPM,
        }

    def save(self, path: str | Path) -> None:
        write_json(path, [asdict(s) for s in self.sessions])

    @classmethod
    def load(cls, path: str | Path) -> "Analytics":
        data = json.loads(Path(path).read_text())
        return cls(sessions=[Session(**row) for row in data])
