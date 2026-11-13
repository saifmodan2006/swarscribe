"""Speech model registry and local cache management.

Models live under ~/.swarscribe/models and are downloaded once, on
first use, from their public sources. Nothing else about SwarScribe
needs the network, ever.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModelInfo:
    name: str
    engine: str
    size_mb: int
    languages: str
    note: str


MODELS = [
    ModelInfo("tiny", "whisper", 75, "99 languages",
              "Fastest. Rough drafts and weak hardware."),
    ModelInfo("base", "whisper", 145, "99 languages",
              "Good default for short dictation on CPU."),
    ModelInfo("small", "whisper", 465, "99 languages",
              "Noticeably better with accents and names."),
    ModelInfo("medium", "whisper", 1530, "99 languages", "Larger multilingual model."),
    ModelInfo("large-v3", "whisper", 3100, "99 languages", "Larger multilingual model."),
    ModelInfo("large-v3-turbo", "whisper", 1620, "99 languages",
              "Best Whisper quality per second. Wants a GPU or patience."),
    ModelInfo("parakeet-tdt-0.6b-v3", "parakeet", 2440, "25 European languages",
              "Optional NVIDIA NeMo backend. Hindi is not supported."),
]

_BY_NAME = {m.name: m for m in MODELS}


def cache_dir() -> Path:
    base = os.environ.get("SWARSCRIBE_HOME")
    root = Path(base) if base else Path.home() / ".swarscribe"
    return root / "models"


def get(name: str) -> ModelInfo:
    if name not in _BY_NAME:
        raise KeyError(f"unknown model {name!r}; known: "
                       + ", ".join(_BY_NAME))
    return _BY_NAME[name]


def is_downloaded(name: str) -> bool:
    root = cache_dir()
    folder = root / name
    if (folder / "model.bin").is_file() and (folder / "config.json").is_file():
        return True
    # faster-whisper caches under Hugging Face style folder names,
    # for example models--Systran--faster-whisper-tiny.
    if root.is_dir():
        return any(candidate.is_file() and (candidate.parent / "config.json").is_file()
                   for candidate in root.glob(f"models--*--faster-whisper-{name}/snapshots/*/model.bin"))
    return False


def status() -> list[dict]:
    return [{"name": m.name, "engine": m.engine, "size_mb": m.size_mb,
             "languages": m.languages, "note": m.note,
             "downloaded": is_downloaded(m.name)} for m in MODELS]


def recommended(hindi: bool = False) -> ModelInfo:
    """The honest default: Parakeet for English speed, Whisper for range."""
    return get("small") if hindi else get("parakeet-tdt-0.6b-v3")
