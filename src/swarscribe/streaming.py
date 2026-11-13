"""Bounded PCM chunk transcription with partial previews and final events."""

from __future__ import annotations

import array
import wave
from dataclasses import dataclass

from .recorder import AudioBuffer, SAMPLE_RATE
from .transcribe import Transcript
from .vad import frame_rms

CHUNK_MS = 100


@dataclass
class StreamEvent:
    kind: str
    text: str
    segment: int
    start_seconds: float = 0.0
    end_seconds: float = 0.0
    timing: str = "chunk"


def _wav_bytes(samples: array.array, rate: int = SAMPLE_RATE) -> bytes:
    buffer = AudioBuffer(rate)
    buffer.add(samples.tobytes())
    return buffer.wav_bytes(trim=False)


class StreamingTranscriber:
    def __init__(self, transcribe_wav, sample_rate: int = SAMPLE_RATE,
                 silence_ms: int = 700, min_segment_ms: int = 400,
                 silence_threshold: float = 300.0, max_segment_ms: int = 20000):
        self._transcribe = transcribe_wav
        self.rate = sample_rate
        self._pause = sample_rate * silence_ms // 1000
        self._minimum = sample_rate * min_segment_ms // 1000
        self._limit = sample_rate * max_segment_ms // 1000
        self.threshold = silence_threshold
        if not 0 < self._minimum <= self._limit or self._pause <= 0:
            raise ValueError("Invalid segment duration limits.")
        self._open = array.array("h")
        self._silent = 0
        self._position = 0
        self._segment = 0
        self._last_partial = ""

    @property
    def position(self) -> float:
        return self._position / self.rate

    def feed(self, pcm: bytes) -> list[StreamEvent]:
        samples = array.array("h")
        samples.frombytes(pcm)
        events = []
        cursor = 0
        while cursor < len(samples):
            count = min(self._limit - len(self._open), len(samples) - cursor)
            part = samples[cursor:cursor + count]
            cursor += count
            self._position += count
            quiet = frame_rms(part) < self.threshold
            if not self._open and quiet:
                continue
            self._open.extend(part)
            self._silent = self._silent + count if quiet else 0
            if self._silent >= self._pause or len(self._open) >= self._limit:
                events.extend(self.flush())
        return events

    def poll_partial(self) -> StreamEvent | None:
        if len(self._open) < self._minimum:
            return None
        output = self._transcribe(_wav_bytes(self._open, self.rate))
        text = (output.text if isinstance(output, Transcript) else output).strip()
        if not text or text == self._last_partial:
            return None
        self._last_partial = text
        return StreamEvent("partial", text, self._segment,
                           (self._position - len(self._open)) / self.rate, self.position)

    def cancel(self) -> None:
        self._open = array.array("h")
        self._silent = 0
        self._last_partial = ""

    def flush(self) -> list[StreamEvent]:
        samples = self._open
        start = (self._position - len(samples)) / self.rate
        self.cancel()
        if len(samples) < self._minimum:
            return []
        output = self._transcribe(_wav_bytes(samples, self.rate))
        if isinstance(output, Transcript) and output.segments:
            events = [StreamEvent("final", segment.text, self._segment, start + segment.start,
                                  start + segment.end, "model")
                      for segment in output.segments]
        else:
            text = (output.text if isinstance(output, Transcript) else output).strip()
            events = [StreamEvent("final", text, self._segment, start, self.position)] if text else []
        if events:
            self._segment += 1
        return events


def iter_file_events(path: str, transcribe_wav, chunk_ms: int = CHUNK_MS,
                     partial_every: float | None = None, **kwargs):
    with wave.open(path, "rb") as handle:
        if handle.getnchannels() != 1 or handle.getsampwidth() != 2:
            raise ValueError("Chunked transcription requires a mono PCM16 WAV.")
        rate = handle.getframerate()
        frames = rate * chunk_ms // 1000
        if frames <= 0:
            raise ValueError("Chunk size is too small.")
        streamer = StreamingTranscriber(transcribe_wav, sample_rate=rate, **kwargs)
        last_poll = 0.0
        while data := handle.readframes(frames):
            yield from streamer.feed(data)
            if partial_every and streamer.position - last_poll >= partial_every:
                last_poll = streamer.position
                event = streamer.poll_partial()
                if event:
                    yield event
        yield from streamer.flush()


def stream_file(path: str, transcribe_wav, chunk_ms: int = CHUNK_MS,
                **kwargs) -> list[StreamEvent]:
    return list(iter_file_events(path, transcribe_wav, chunk_ms, **kwargs))
