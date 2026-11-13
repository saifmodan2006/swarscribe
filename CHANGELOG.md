# Changelog

## v0.2.0, 2026-11-13

### New
- **Smart formats**: spoken emails, websites, times, dates and amounts land written (5:30 PM, 15 November 2026, 500 rupees, name@domain.com).
- **Auto-learn**: FlowScribe learns personal dictionary entries from your hand edits (`learn.py`, `Pipeline.learn`).
- **Command chains**: "make it formal and shorten it" runs voice macros in one breath.
- **Translation mode**: English and Hindi phrasebook offline, with an optional local LLM layer for full sentences.
- **Session history**: undo and Markdown export for every dictation session.
- **Edit stats on every result**: raw words, clean words, and how many edits the pipeline made for you.
- Web demo redesigned: hero, one-tap examples, live session counters, comparison table, installable PWA manifest.
- Project polish: logo and banner, GitHub Actions CI on Python 3.10 to 3.12, issue and PR templates, CONTRIBUTING and SECURITY guides.

### Faster
- Cleanup patterns are precompiled at import and a benchmark ships in `benchmarks/`. The pipeline processes dictation far faster than speech arrives, on the device, with zero network calls.

## v0.1.0, 2026-11-13

- First release: dual-engine transcription layer (Parakeet plus faster-whisper), smart cleanup with self-correction resolution, personal dictionary, snippets, per-app styles, Command Mode, Code Mode, Meeting Mode, local analytics, FastAPI API, CLI, desktop paste-at-cursor, and a zero-backend web demo. 24 tests.
