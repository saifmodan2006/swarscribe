"""Local speech engines. Text-only callers do not need to load a model."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from threading import RLock
from typing import Protocol

from .models import cache_dir


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    text: str
    engine: str
    language: str | None = None
    segments: tuple[Segment, ...] = ()


class Backend(Protocol):
    def transcribe(self, audio_path: str, language: str | None = None) -> Transcript: ...


class BackendUnavailable(RuntimeError):
    """A model cannot be initialized with the requested settings."""


class TranscriptionError(RuntimeError):
    """A configured speech model could not process the audio."""


def normalize_language(language: str | None) -> str | None:
    return None if not language or language in {"auto", "hinglish"} else language


class FasterWhisperBackend:
    name = "faster-whisper"

    def __init__(self, model: str = "base", download_root: str | None = None,
                 *, device: str = "cpu", local_only: bool = False):
        try:
            from faster_whisper import WhisperModel
        except (ImportError, OSError) as exc:
            raise BackendUnavailable(
                "Whisper runtime unavailable. Install 'swarscribe[whisper]' and check "
                "whether the OS permits CTranslate2 to load its native libraries."
            ) from exc
        try:
            self._model = WhisperModel(
                model, device=device,
                compute_type={"cpu": "int8", "cuda": "float16"}.get(device, "auto"),
                download_root=download_root or str(cache_dir()),
                local_files_only=local_only)
        except Exception as exc:
            hint = ("Download the model first with swarscribe model-download."
                    if local_only else "Check the model name, network/cache and device; try CPU.")
            raise BackendUnavailable(f"Cannot load Whisper {model!r}. {hint}") from exc
        self._lock = RLock()

    def transcribe(self, audio_path: str, language: str | None = None) -> Transcript:
        try:
            from .audio import decode_mono
            audio = decode_mono(audio_path)
            with self._lock:
                segments, info = self._model.transcribe(
                    audio, language=normalize_language(language), task="transcribe",
                    vad_filter=True)
                timed = tuple(Segment(s.start, s.end, s.text.strip())
                              for s in segments if s.text.strip())
        except Exception as exc:
            raise TranscriptionError(
                "Whisper inference failed. Check the audio format and device; "
                "for CUDA check the CTranslate2 CUDA and cuDNN requirements."
            ) from exc
        return Transcript(" ".join(s.text for s in timed), self.name, info.language, timed)


# Languages supported by the bundled Parakeet TDT v3 model.
PARAKEET_LANGUAGES = frozenset(
    "bg hr cs da nl en et fi fr de el hu it lv lt mt pl pt ro sk sl es sv ru uk".split()
)


class ParakeetBackend:
    name = "parakeet"

    def __init__(self, model: str = "nvidia/parakeet-tdt-0.6b-v3", *,
                 device: str = "cpu", local_only: bool = False):
        if local_only and not model.endswith(".nemo"):
            raise BackendUnavailable("Offline Parakeet requires a local .nemo checkpoint.")
        try:
            import torch
            from nemo.collections.asr.models import ASRModel
            from av import AudioFrame  # noqa: F401 -- audio decoding is required too
        except (ImportError, OSError) as exc:
            raise BackendUnavailable(
                "Parakeet runtime unavailable. Install 'swarscribe[parakeet]' "
                "on a NeMo-supported platform, or select Whisper."
            ) from exc
        try:
            target = torch.device("cuda" if device == "auto" and torch.cuda.is_available()
                                  else "cpu" if device == "auto" else device)
            if model.endswith(".nemo"):
                self._model = ASRModel.restore_from(model, map_location=target)
            else:
                self._model = ASRModel.from_pretrained(model, map_location=target)
            self._model = self._model.to(target).eval()
        except Exception as exc:
            raise BackendUnavailable(
                "Cannot load Parakeet. Check the checkpoint and device, or select Whisper."
            ) from exc
        self._lock = RLock()

    def transcribe(self, audio_path: str, language: str | None = None) -> Transcript:
        _check_parakeet_language(language)
        try:
            from .audio import decode_mono
            samples = decode_mono(audio_path)
            with self._lock:
                out = self._model.transcribe([samples], batch_size=1)
            first = out[0] if out else ""
            if isinstance(first, tuple):
                first = first[0]
            text = first if isinstance(first, str) else first.text
        except Exception as exc:
            raise TranscriptionError(
                "Parakeet inference failed. Check the audio and available CPU/GPU memory."
            ) from exc
        # The multilingual model does not accept a forced language hint.
        return Transcript(text.strip(), self.name)


def _check_parakeet_language(language: str | None) -> None:
    if language not in (None, "auto") and language not in PARAKEET_LANGUAGES:
        raise BackendUnavailable(f"Parakeet does not support {language!r}. Select Whisper.")


class EchoBackend:
    """Explicitly injected test backend."""

    name = "echo"

    def __init__(self, text: str = ""):
        self._text = text

    def transcribe(self, audio_path: str, language: str | None = None) -> Transcript:
        return Transcript(self._text, self.name, language)


def transcribe_file(path: str, backend: Backend | None = None,
                    language: str | None = None) -> Transcript:
    return (backend or choose_backend(language=language)).transcribe(path, language)


def transcribe_wav_bytes(data: bytes, backend: Backend | None = None,
                         language: str | None = None) -> Transcript:
    fd, path = tempfile.mkstemp(suffix=".wav")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        return transcribe_file(path, backend, language)
    finally:
        os.unlink(path)


@lru_cache(maxsize=2)
def _load(engine: str, model: str | None, device: str,
          local_only: bool, root: str) -> Backend:
    if engine == "parakeet":
        return ParakeetBackend(model or "nvidia/parakeet-tdt-0.6b-v3",
                               device=device, local_only=local_only)
    return FasterWhisperBackend(model or "base", download_root=root,
                                device=device, local_only=local_only)


_load_lock = RLock()


def choose_backend(preference: str = "auto", language: str | None = None,
                   model: str | None = None, *, device: str = "cpu",
                   local_only: bool = False) -> Backend:
    """Honor explicit engines; auto uses Whisper for multilingual or pinned models."""
    if preference not in {"auto", "whisper", "parakeet"}:
        raise BackendUnavailable(f"Unknown speech engine {preference!r}. Use auto, whisper or parakeet.")
    if device not in {"cpu", "cuda", "auto"}:
        raise BackendUnavailable("Choose cpu, cuda or auto for the speech device.")
    if preference == "parakeet":
        _check_parakeet_language(language)
    order = (preference,)
    if preference == "auto":
        order = ("parakeet", "whisper") if language == "en" and not model and not local_only else ("whisper",)
    errors = []
    with _load_lock:
        for engine in order:
            try:
                return _load(engine, model, device, local_only, str(cache_dir()))
            except BackendUnavailable as exc:
                errors.append(str(exc))
    raise BackendUnavailable(" ".join(errors))
