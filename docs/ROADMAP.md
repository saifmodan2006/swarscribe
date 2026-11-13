# Roadmap

## v0.1 (shipped 2026-11-13)
- Dual-engine transcription layer (Parakeet + faster-whisper)
- Smart cleanup pipeline with self-correction resolution
- Personal dictionary, snippets, per-app styles
- Command Mode, Code Mode, Meeting Mode
- Local analytics, FastAPI service, CLI, web demo, desktop typing

## v0.2 (shipped 2026-11-13)
- Smart formats: emails, websites, times, dates, amounts
- Auto-learn dictionary from hand edits
- Command chains (voice macros)
- Translation mode: offline phrasebook plus optional local LLM
- Session history with undo and Markdown export, edit stats
- Precompiled cleanup engine and a shipped benchmark
- Redesigned web demo, logo and banner, CI, contributor guides

## v0.3
- Streaming dictation: words appear while you speak (Parakeet streaming)
- Tauri desktop shell with a proper settings window and tray icon
- One-tap dictionary review UI for auto-learned pairs

## v0.4
- Android floating-bubble dictation (the OpenWhispr route)
- Team dictionaries and shared snippets as plain Git-synced files
- Plugin API so any app can embed the cleanup pipeline

## v1.0
- Signed installers for Mac, Windows and Linux
- Benchmarks published against the Open ASR Leaderboard sets
- Optional self-hosted sync, encrypted, off by default

Ideas and pull requests are welcome. Keep PRs small and tested,
the same rule as any good open source project.
