"""Streaming dictation: words land while you are still speaking.

The transcriber buffers incoming PCM chunks. Whenever a pause of
``silence_ms`` or more is detected (energy VAD), the open segment is
finalized: transcribed once and yielded as a final event. Between
finalizations, ``poll_partial`` re-transcribes the open segment so a UI
can show live partial text. Final text is stable and never rewritten,
which is the contract a dictation UI actually needs.
"""

from __future__ import annotations

import array
import io
import wave
from dataclasses import dataclass, field

from .recorder import AudioBuffer, SAMPLE_RATE
from .vad import frame_rms

CHUNK_MS = 100


@dataclass
class StreamEvent:
    kind: str          # "partial" or "final"
    text: str
    segment: int


def _wav_bytes(samples: array.array, rate: int = SAMPLE_RATE) -> bytes:
    buffer = AudioBuffer(rate)
    buffer.add(samples.tobytes())
    return buffer.wav_bytes(trim=False)


class StreamingTranscriber:
    """Feed PCM16 chunks, get partial and final transcript events."""

    def __init__(self, transcribe_wav, sample_rate: int = SAMPLE_RATE,
                 silence_ms: int = 700, min_segment_ms: int = 400,
                 silence_threshold: float = 300.0):
        # transcribe_wav: callable(bytes) -> str for one WAV segment
        self._transcribe = transcribe_wav
        self.rate = sample_rate
        self.silence_ms = silence_ms
        self.min_segment_ms = min_segment_ms
        self.threshold = silence_threshold
        self._open = array.array("h")
        self._silence_run = 0
        self._segment = 0
        self._last_partial = ""

    def _chunk_is_silence(self, samples: array.array) -> bool:
        return frame_rms(samples) < self.threshold

    def feed(self, pcm: bytes) -> list[StreamEvent]:
        """Add one chunk of PCM16 audio; returns any finalized events."""
        samples = array.array("h")
        samples.frombytes(pcm)
        self._open.extend(samples)
        chunk_ms = int(len(samples) / self.rate * 1000)
        if self._chunk_is_silence(samples):
            self._silence_run += max(chunk_ms, 1)
        else:
            self._silence_run = 0
        events: list[StreamEvent] = []
        open_ms = int(len(self._open) / self.rate * 1000)
        if self._silence_run >= self.silence_ms and open_ms >= self.min_segment_ms:
            event = self._finalize()
            if event:
                events.append(event)
        return events

    def poll_partial(self) -> StreamEvent | None:
        """Transcribe the open segment for a live preview, if it changed."""
        if len(self._open) < self.rate * self.min_segment_ms // 1000:
            return None
        text = self._transcribe(_wav_bytes(self._open, self.rate)).strip()
        if not text or text == self._last_partial:
            return None
        self._last_partial = text
        return StreamEvent("partial", text, self._segment)

    def _finalize(self) -> StreamEvent | None:
        samples = self._open
        self._open = array.array("h")
        self._silence_run = 0
        self._last_partial = ""
        if len(samples) < self.rate * self.min_segment_ms // 1000:
            return None
        text = self._transcribe(_wav_bytes(samples, self.rate)).strip()
        self._segment += 1
        if not text:
            return None
        return StreamEvent("final", text, self._segment - 1)

    def flush(self) -> list[StreamEvent]:
        """Finalize whatever is left when the speaker stops."""
        event = self._finalize()
        return [event] if event else []


def stream_file(path: str, transcribe_wav, chunk_ms: int = CHUNK_MS,
                **kwargs) -> list[StreamEvent]:
    """Replay a WAV file through the streamer (demos, tests, imports)."""
    with wave.open(path, "rb") as handle:
        rate = handle.getframerate()
        frames_per_chunk = rate * chunk_ms // 1000
        streamer = StreamingTranscriber(transcribe_wav, sample_rate=rate,
                                        **kwargs)
        events: list[StreamEvent] = []
        while True:
            data = handle.readframes(frames_per_chunk)
            if not data:
                break
            events.extend(streamer.feed(data))
        events.extend(streamer.flush())
        return events
