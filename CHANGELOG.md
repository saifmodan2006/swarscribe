# Changelog

## v0.3.0, 2026-11-13

### The rebrand
- **FlowScribe is now SwarScribe.** The old name was already used by a Chrome extension, a Webflow SEO product, an AppSumo listing and an n8n documentation tool. SwarScribe (Swar, voice, plus Scribe) had no product, app or GitHub repository using it in exact searches, so the name is now fully this project's. The GitHub repo was renamed, and the old URL redirects here.
- **New identity:** a logo built on one idea, a voice wave landing as a text cursor, in Swar Coral to Marigold with Palm Teal on Ink. Full system in `docs/BRANDING.md` and `assets/` (icon, horizontal lockup, mono mark, banner).
- **New motto:** "Say it. It is written."
- Package, CLI and config all renamed: `pip install swarscribe`, the `swarscribe` command, config at `~/.swarscribe/config.json`. Behaviour is unchanged from v0.2.0, all 43 tests pass under the new name.

## v0.2.0, 2026-11-13 (released as FlowScribe)

### New
- **Smart formats**: spoken emails, websites, times, dates and amounts land written (5:30 PM, 15 November 2026, 500 rupees, name@domain.com).
- **Auto-learn**: SwarScribe learns personal dictionary entries from your hand edits (`learn.py`, `Pipeline.learn`).
- **Command chains**: "make it formal and shorten it" runs voice macros in one breath.
- **Translation mode**: English and Hindi phrasebook offline, with an optional local LLM layer for full sentences.
- **Session history**: undo and Markdown export for every dictation session.
- **Edit stats on every result**: raw words, clean words, and how many edits the pipeline made for you.
- Web demo redesigned: hero, one-tap examples, live session counters, comparison table, installable PWA manifest.
- Project polish: logo and banner, GitHub Actions CI on Python 3.10 to 3.12, issue and PR templates, CONTRIBUTING and SECURITY guides.

### Faster
- Cleanup patterns are precompiled at import and a benchmark ships in `benchmarks/`. The pipeline processes dictation far faster than speech arrives, on the device, with zero network calls.

## v0.1.0, 2026-11-13 (released as FlowScribe)

- First release: dual-engine transcription layer (Parakeet plus faster-whisper), smart cleanup with self-correction resolution, personal dictionary, snippets, per-app styles, Command Mode, Code Mode, Meeting Mode, local analytics, FastAPI API, CLI, desktop paste-at-cursor, and a zero-backend web demo. 24 tests.
