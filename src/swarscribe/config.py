"""User preferences, dictionary and snippets stored as local JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .dictionary import PersonalDictionary
from .models import cache_dir
from .snippets import SnippetLibrary
from .storage import write_json

DEFAULT_PATH = Path.home() / ".swarscribe" / "config.json"
MODES = ("normal", "smart", "code", "command", "meeting")


@dataclass
class Config:
    engine: str = "auto"
    language: str | None = None
    model: str | None = None
    device: str = "cpu"
    local_only: bool = False
    microphone: int | str | None = None
    hotkey: str = "ctrl+win"
    toggle: bool = False
    mode: str = "smart"
    style: str | None = None
    keep_history: bool = True
    history_days: int = 30
    ollama_model: str | None = None
    dictionary: dict[str, str] = field(default_factory=dict)
    snippets: dict[str, str] = field(default_factory=dict)
    app_styles: dict[str, str] = field(default_factory=dict)

    def to_dictionary(self) -> PersonalDictionary:
        dictionary = PersonalDictionary()
        for heard, correct in self.dictionary.items():
            dictionary.add(heard, correct)
        return dictionary

    def to_snippets(self) -> SnippetLibrary:
        library = SnippetLibrary()
        for trigger, expansion in self.snippets.items():
            library.add(trigger, expansion)
        return library

    def backend(self):
        from .transcribe import choose_backend
        return choose_backend(self.engine, self.language, self.model,
                              device=self.device, local_only=self.local_only)

    def pipeline(self):
        from .pipeline import Pipeline
        return Pipeline(dictionary=self.to_dictionary(), snippets=self.to_snippets())

    def save(self, path: Path | None = None) -> Path:
        path = path if path is not None else cache_dir().parent / "config.json"
        write_json(path, vars(self))
        return Path(path)

    @classmethod
    def load(cls, path: Path | None = None) -> Config:
        path = Path(path) if path is not None else cache_dir().parent / "config.json"
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
