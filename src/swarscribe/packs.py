"""Shareable word packs: dictionaries and snippets as portable JSON.

A pack is one JSON file with a name, dictionary entries and snippets.
Export your pack, share it, and anyone can import it in one command.
Packs live in the repo under packs/ and travel like any other file.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .config import Config


@dataclass
class Pack:
    name: str
    dictionary: dict[str, str] = field(default_factory=dict)
    snippets: dict[str, str] = field(default_factory=dict)

    def save(self, path: Path) -> Path:
        path.write_text(json.dumps(
            {"name": self.name, "dictionary": self.dictionary,
             "snippets": self.snippets}, indent=2))
        return path

    @classmethod
    def load(cls, path: Path) -> "Pack":
        data = json.loads(Path(path).read_text())
        return cls(name=data.get("name", Path(path).stem),
                   dictionary=data.get("dictionary", {}),
                   snippets=data.get("snippets", {}))


def export_pack(config: Config, name: str) -> Pack:
    return Pack(name=name, dictionary=dict(config.dictionary),
                snippets=dict(config.snippets))


def import_pack(pack: Pack, config: Config) -> int:
    """Merge a pack into a config; returns how many entries were added."""
    added = 0
    for heard, correct in pack.dictionary.items():
        if heard not in config.dictionary:
            added += 1
        config.dictionary[heard] = correct
    for trigger, expansion in pack.snippets.items():
        if trigger not in config.snippets:
            added += 1
        config.snippets[trigger] = expansion
    return added
