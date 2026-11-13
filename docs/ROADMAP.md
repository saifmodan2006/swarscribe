# Roadmap

## v0.1 (shipped 2026-11-13, as FlowScribe)
- Dual-engine transcription layer (Parakeet + faster-whisper)
- Smart cleanup pipeline with self-correction resolution
- Personal dictionary, snippets, per-app styles
- Command Mode, Code Mode, Meeting Mode
- Local analytics, FastAPI service, CLI, web demo, desktop typing

## v0.2 (shipped 2026-11-13, as FlowScribe)
- Smart formats: emails, websites, times, dates, amounts
- Auto-learn dictionary from hand edits
- Command chains (voice macros)
- Translation mode: offline phrasebook plus optional local LLM
- Session history with undo and Markdown export, edit stats
- Precompiled cleanup engine and a shipped benchmark
- Redesigned web demo, logo and banner, CI, contributor guides

## v0.3 (shipped 2026-11-13)
- The rebrand: FlowScribe became SwarScribe, new logo, colours and motto

## v0.4 (shipped 2026-11-13)
- Real desktop app: recorder, VAD silence trimming, model manager,
  push-to-talk loop, verified end-to-end transcription
- Dashboard: stats, models and dictionary API plus a web dashboard page
- Android companion app and system keyboard, Kotlin cleanup port,
  on-device recognition and desktop server mode, APK built by CI

## v0.5
- Streaming dictation: words appear while you speak (Parakeet streaming)
- Tauri desktop shell with a proper settings window and tray icon
- Run the Android app on a physical phone, tune the keyboard UX
- One-tap dictionary review UI for auto-learned pairs

## v0.6
- iOS companion app and keyboard extension (dictation round-trips
  through the app, the route Apple allows)
- Team dictionaries and shared snippets as plain Git-synced files
- Plugin API so any app can embed the cleanup pipeline

## v1.0
- Signed installers for Mac, Windows and Linux, Play Store listing
- Benchmarks published against the Open ASR Leaderboard sets
- Optional self-hosted sync, encrypted, off by default

Ideas and pull requests are welcome. Keep PRs small and tested,
the same rule as any good open source project.
