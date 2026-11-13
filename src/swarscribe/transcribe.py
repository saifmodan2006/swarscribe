"""Dual-engine transcription, all open source.

SwarScribe does not bet on one speech model:

- Parakeet TDT 0.6B v3 (NVIDIA, via NeMo): fastest and most accurate
  on English and 25 European languages. The live-dictation engine.
- Whisper large-v3-turbo (OpenAI, MIT) via faster-whisper or
  whisper.cpp: 99 languages, including Hindi. The coverage engine.
- Hinglish mode: Whisper with a language hint, then the cleanup
  pipeline, for the way people in India actually speak.

Backends load lazily and degrade gracefully: if no model library is
installed, the pipeline still runs in text-in mode (type or paste a
rough transcript, get SwarScribe-clean output), which is also how
the web demo and the test suite work anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Transcript:
    text: str
    engine: str
    language: str | None = None


class BackendUnavailable(RuntimeError):
    pass


class FasterWhisperBackend:
    name = "faster-whisper"

    def __init__(self, model: str = "large-v3-turbo",
                 download_root: str | None = None):
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise BackendUnavailable(
                "faster-whisper is not installed. "
                "Install with: pip install swarscribe[whisper]") from exc
        if download_root is None:
            from .models import cache_dir
            download_root = str(cache_dir())
        self._model = WhisperModel(model, compute_type="auto",
                                   download_root=download_root)

    def transcribe(self, audio_path: str,
                   language: str | None = None) -> Transcript:
        segments, info = self._model.transcribe(audio_path,
                                                language=language)
        text = " ".join(seg.text.strip() for seg in segments)
        return Transcript(text=text, engine=self.name,
                          language=getattr(info, "language", language))


class ParakeetBackend:
    name = "parakeet"

    def __init__(self, model: str = "nvidia/parakeet-tdt-0.6b-v3"):
        try:
            import nemo.collections.asr as nemo_asr
        except ImportError as exc:
            raise BackendUnavailable(
                "NeMo is not installed. "
                "Install with: pip install swarscribe[parakeet]") from exc
        self._model = nemo_asr.models.ASRModel.from_pretrained(model)

    def transcribe(self, audio_path: str,
                   language: str | None = None) -> Transcript:
        out = self._model.transcribe([audio_path])
        first = out[0]
        text = getattr(first, "text", str(first))
        return Transcript(text=text, engine=self.name, language=language)


class EchoBackend:
    """Text-in backend: returns a supplied transcript unchanged.

    Used by the web demo, the CLI `clean` command and the tests, so
    the whole cleanup pipeline is usable with zero model downloads.
    """

    name = "echo"

    def __init__(self, text: str = ""):
        self._text = text

    def transcribe(self, audio_path: str,
                   language: str | None = None) -> Transcript:
        return Transcript(text=self._text, engine=self.name,
                          language=language)


def transcribe_file(path: str, backend=None,
                    language: str | None = None) -> Transcript:
    """Transcribe an audio file with the chosen (or best) backend."""
    backend = backend or choose_backend(language=language)
    return backend.transcribe(path, language=language)


def transcribe_wav_bytes(data: bytes, backend=None,
                         language: str | None = None) -> Transcript:
    """Transcribe in-memory WAV bytes (the recorder's output)."""
    import os
    import tempfile
    backend = backend or choose_backend(language=language)
    fd, path = tempfile.mkstemp(suffix=".wav")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        return backend.transcribe(path, language=language)
    finally:
        os.unlink(path)


def choose_backend(preference: str = "auto", language: str | None = None,
                   model: str | None = None):
    """Pick the best available engine.

    English live dictation prefers Parakeet (speed). Any other
    language, including Hindi and Hinglish, prefers Whisper.
    Falls back to EchoBackend when no model library is present.
    """
    want_parakeet = preference == "parakeet" or (
        preference == "auto" and language in (None, "en"))
    order = [ParakeetBackend, FasterWhisperBackend] if want_parakeet \
        else [FasterWhisperBackend, ParakeetBackend]
    if preference == "whisper":
        order = [FasterWhisperBackend]
    if preference == "echo":
        return EchoBackend()
    for cls in order:
        try:
            if cls is FasterWhisperBackend and model:
                return cls(model=model)
            return cls()
        except BackendUnavailable:
            continue
    return EchoBackend()
