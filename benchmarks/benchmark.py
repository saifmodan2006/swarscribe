"""Cleanup speed benchmark.

Run: python benchmarks/benchmark.py

The cleanup pipeline is the part of SwarScribe that runs on every
single dictation, so it is built to be boring and fast: precompiled
patterns, no model calls, no I/O. This script times it honestly on
whatever machine runs it and prints words per second.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from swarscribe.cleanup import clean_text

SAMPLE = (
    "um the meeting is on monday no wait tuesday at five thirty pm "
    "comma and uh please send five hundred rupees to rahul comma "
    "and check devbysaif dot in for the details period my email is "
    "saif modan at gmail dot com "
) * 20

RUNS = 200


def main() -> None:
    clean_text(SAMPLE)  # warm up
    start = time.perf_counter()
    for _ in range(RUNS):
        out = clean_text(SAMPLE)
    elapsed = time.perf_counter() - start
    words = len(SAMPLE.split()) * RUNS
    print(f"sample words per run : {len(SAMPLE.split())}")
    print(f"runs                 : {RUNS}")
    print(f"total time           : {elapsed:.3f}s")
    print(f"per dictation        : {elapsed / RUNS * 1000:.2f} ms")
    print(f"throughput           : {words / elapsed:,.0f} words/second")
    print(f"example output       : {out[:110]}...")


if __name__ == "__main__":
    main()
