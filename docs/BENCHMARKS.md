# Benchmarks, measured not marketed

Every number here was produced by `benchmarks/benchmark_asr.py` in
this repo, on a small shared cloud CPU (1.5 vCPU), on 2026-11-13.
Rerun it on your own machine; your numbers will differ and that is
the point.

## Speech recognition (JFK sample clip, 11 seconds, reference known)

| Engine | Word error rate | Time for 11s audio | Speed |
| --- | --- | --- | --- |
| faster-whisper tiny | 0.000 | 1.29 s | 8.5x real time |
| faster-whisper base | 0.000 | 2.11 s | 5.2x real time |

Method: standard WER with case and punctuation normalized, the usual
scoring convention. The clip is short and clean, so treat 0.000 as
"this clip, perfectly", not as a universal claim. Noisier audio,
accents and long files will score worse, for every engine, including
the cloud ones. Larger models (small, medium, large-v3-turbo) trade
speed for accuracy on hard audio; SwarScribe lets you pick.

## Cleanup pipeline

About 63,000 words per second (roughly 11 ms for a 680-word
dictation) on the same small CPU. Cleanup is never the bottleneck;
transcription is, which is why the models run locally and stream.

## About comparing with Wispr Flow

Wispr is a hosted cloud service: its accuracy and latency cannot be
measured locally, offline, or reproducibly, and its numbers depend on
their servers and your network. What can be compared is on the record
in [COMPARISON.md](COMPARISON.md): price, caps, privacy model, and
features. On speed, a local engine at 5 to 8x real time on a weak CPU
means dictation keeps up with speech with room to spare, with no
network round trip at all.
