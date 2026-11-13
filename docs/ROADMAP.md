# Roadmap

## v0.1 (this release)
- Dual-engine transcription layer (Parakeet + faster-whisper)
- Smart cleanup pipeline with self-correction resolution
- Personal dictionary, snippets, per-app styles
- Command Mode, Code Mode, Meeting Mode
- Local analytics, FastAPI service, CLI, web demo, desktop typing

## v0.2
- Streaming dictation: words appear while you speak (Parakeet streaming)
- Auto-learn dictionary: one-tap add when you correct a word
- Translation mode: speak Hindi, land English text (local LLM pass)
- Tauri desktop shell with a proper settings window and tray icon

## v0.3
- Android floating-bubble dictation (the OpenWhispr route)
- Team dictionaries and shared snippets as plain Git-synced files
- Plugin API so any app can embed the cleanup pipeline

## v1.0
- Signed installers for Mac, Windows and Linux
- Benchmarks published against the Open ASR Leaderboard sets
- Optional self-hosted sync, encrypted, off by default

Ideas and pull requests are welcome. Keep PRs small and tested,
the same rule as any good open source project.
