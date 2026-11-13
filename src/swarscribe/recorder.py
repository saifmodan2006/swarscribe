"""Microphone capture for the desktop app.

Recording uses sounddevice when it is installed (the `desktop` extra);
everything downstream of capture, buffering, WAV writing, VAD trimming
and duration maths, is pure standard library so it can be tested
anywhere, including CI machines with no microphone at all.
"""
from __future__ import annotations

import array
import io
import wave

from .vad import is_silence, trim_silence

SAMPLE_RATE = 16000


class AudioBuffer:
    """Accumulates 16-bit mono frames and renders WAV bytes."""

    def __init__(self, rate: int = SAMPLE_RATE):
        self.rate = rate
        self._chunks: list[bytes] = []

    def add(self, data: bytes) -> None:
        if data:
            self._chunks.append(data)

    def samples(self) -> array.array:
        out = array.array("h")
        out.frombytes(b"".join(self._chunks))
        return out

    @property
    def seconds(self) -> float:
        return len(self.samples()) / self.rate

    def wav_bytes(self, trim: bool = True) -> bytes:
        samples = self.samples()
        if trim:
            samples = trim_silence(samples)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(self.rate)
            w.writeframes(samples.tobytes())
        return buf.getvalue()

    def silent(self) -> bool:
        return is_silence(self.samples())


class Recorder:
    """Push-to-talk recorder. start(), speak, stop() returns the buffer."""

    def __init__(self, rate: int = SAMPLE_RATE):
        self.rate = rate
        self.buffer = AudioBuffer(rate)
        self._stream = None

    def start(self) -> None:
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError(
                "Recording needs the desktop extra: "
                "pip install 'swarscribe[desktop]'") from exc
        self.buffer = AudioBuffer(self.rate)

        def _callback(indata, frames, time_info, status):  # pragma: no cover
            self.buffer.add(bytes(indata))

        self._stream = sd.RawInputStream(
            samplerate=self.rate, channels=1, dtype="int16",
            callback=_callback)
        self._stream.start()

    def stop(self) -> AudioBuffer:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        return self.buffer
