"""Honest ASR benchmark: word error rate and speed, on your machine.

Runs faster-whisper models against sample clips with known reference
transcripts and prints WER plus real-time factor. No cherry-picking:
the clips and references ship in the repo, and anyone can rerun this.

    python benchmarks/benchmark_asr.py [path-to-jfk.wav]

Wispr Flow is a cloud service, so it cannot be benchmarked locally or
offline; this measures the engines SwarScribe itself ships.
"""

from __future__ import annotations

import difflib
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from swarscribe.cleanup import clean_text  # noqa: E402

REFERENCE_JFK = ("and so my fellow americans ask not what your country "
                 "can do for you ask what you can do for your country")


def _words(text: str) -> list[str]:
    import re
    return re.sub(r"[^a-z0-9 ]", " ", text.lower()).split()


def wer(reference: str, hypothesis: str) -> float:
    """Standard WER: case and punctuation normalized before scoring."""
    ref = _words(reference)
    hyp = _words(hypothesis)
    matcher = difflib.SequenceMatcher(a=ref, b=hyp)
    errors = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            errors += max(i2 - i1, j2 - j1)
    return errors / max(len(ref), 1)


def main() -> None:
    from swarscribe.transcribe import FasterWhisperBackend, transcribe_file

    clip = sys.argv[1] if len(sys.argv) > 1 else "jfk.wav"
    duration = 11.0  # the JFK sample clip, seconds
    for model in ("tiny", "base"):
        backend = FasterWhisperBackend(model=model)
        start = time.perf_counter()
        result = transcribe_file(clip, backend=backend)
        elapsed = time.perf_counter() - start
        print(f"faster-whisper {model:5s}  WER {wer(REFERENCE_JFK, result.text):.3f}"
              f"  {elapsed:.2f}s for {duration:.0f}s audio"
              f"  ({duration / elapsed:.1f}x real time)")
        print(f"  heard: {result.text}")

    sample = ("um the meeting is on monday no wait tuesday at five comma "
              "and please check my portfolio ") * 40
    start = time.perf_counter()
    for _ in range(50):
        clean_text(sample)
    per_call = (time.perf_counter() - start) / 50
    words = len(sample.split())
    print(f"cleanup: {words / per_call:,.0f} words/second "
          f"({per_call * 1000:.1f} ms per {words}-word dictation)")


if __name__ == "__main__":
    main()
