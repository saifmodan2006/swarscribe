"""Tiny energy based voice activity detection, pure standard library.

Dictation audio is 16 kHz mono 16-bit PCM. The VAD works on frames of
samples, measures each frame's RMS energy, and answers two questions:
where does speech start and end (so recordings can be trimmed), and is
this chunk silence (so empty recordings never reach the model).
"""
from __future__ import annotations

import array
import math

SAMPLE_RATE = 16000
FRAME_MS = 30


def frame_rms(frame: array.array) -> float:
    if not frame:
        return 0.0
    return math.sqrt(sum(s * s for s in frame) / len(frame))


def frames_of(samples: array.array, frame_ms: int = FRAME_MS,
              rate: int = SAMPLE_RATE):
    size = max(1, int(rate * frame_ms / 1000))
    for i in range(0, len(samples), size):
        yield samples[i:i + size]


def speech_bounds(samples: array.array, threshold: float = 300.0,
                  pad_frames: int = 3, frame_ms: int = FRAME_MS,
                  rate: int = SAMPLE_RATE) -> tuple[int, int]:
    """Sample indices (start, end) of the speech region.

    Frames above the energy threshold count as speech; a small pad of
    frames on each side keeps soft beginnings and endings intact. All
    silence returns (0, 0).
    """
    frames = list(frames_of(samples, frame_ms, rate))
    if not frames:
        return (0, 0)
    loud = [i for i, f in enumerate(frames) if frame_rms(f) > threshold]
    if not loud:
        return (0, 0)
    size = max(1, int(rate * frame_ms / 1000))
    first = max(0, loud[0] - pad_frames)
    last = min(len(frames) - 1, loud[-1] + pad_frames)
    return (first * size, min(len(samples), (last + 1) * size))


def trim_silence(samples: array.array, **kwargs) -> array.array:
    start, end = speech_bounds(samples, **kwargs)
    if end <= start:
        return array.array("h")
    return samples[start:end]


def is_silence(samples: array.array, threshold: float = 300.0) -> bool:
    return speech_bounds(samples, threshold=threshold) == (0, 0)
