"""User configuration, stored locally as plain JSON.

Lives at ~/.flowscribe/config.json. Holds the personal dictionary,
snippets, preferred engine and per-app styles. Nothing is synced
anywhere unless the user puts the file there themselves.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .dictionary import PersonalDictionary
from .snippets import SnippetLibrary

DEFAULT_PATH = Path.home() / ".flowscribe" / "config.json"


@dataclass
class Config:
    engine: str = "auto"
    language: str | None = None
    hotkey: str = "ctrl+win"
    dictionary: dict[str, str] = field(default_factory=dict)
    snippets: dict[str, str] = field(default_factory=dict)
    app_styles: dict[str, str] = field(default_factory=dict)

    def to_dictionary(self) -> PersonalDictionary:
        d = PersonalDictionary()
        for heard, correct in self.dictionary.items():
            d.add(heard, correct)
        return d

    def to_snippets(self) -> SnippetLibrary:
        lib = SnippetLibrary()
        for trigger, expansion in self.snippets.items():
            lib.add(trigger, expansion)
        return lib

    def save(self, path: Path = DEFAULT_PATH) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.__dict__, indent=2))
        return path

    @classmethod
    def load(cls, path: Path = DEFAULT_PATH) -> "Config":
        if not Path(path).exists():
            return cls()
        data = json.loads(Path(path).read_text())
        return cls(**{k: v for k, v in data.items()
                      if k in cls.__dataclass_fields__})
