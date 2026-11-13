# Changelog

## Unreleased

- Require a real speech engine for audio and provide setup errors. Add CPU/GPU selection, cached-only Whisper, bounded partial/final events and real audio timestamps.
- Replace the Windows key-release loop with a single hotkey worker. Check editor focus, support toggle recording and preview selection commands.
- Serve the dashboard and data from one loopback origin. Share dictionary, snippets, settings and transcript history across Python surfaces.
- Isolate Android pairing behind authenticated HTTPS. Require the Android on-device recognizer for offline keyboard input.
- Fix browser speech disclosures, SwarScribe branding, spoken times/dates/amounts and demo controls.
- Add API, Windows state, Android and web regression tests and build checks. The project remains alpha.

## v0.6.0, 2026-11-13

### Everywhere release
- **Streaming dictation** (`streaming.py`): pause-segmented live transcription with partial and final events, verified on real speech streamed in chunks.
- **Voice-note bots** (`bots/`): Telegram bot that turns voice notes into clean text (tested end to end with fakes), plus a WhatsApp Cloud API webhook with tested parsing and reply building.
- **Meeting recorder** (`swarscribe meeting-record`): a WAV becomes timestamped Markdown notes with summary, decisions and action items. No fake speaker guessing.
- **Hinglish mode** (`clean --hinglish`, docs/HINGLISH.md): cleanup that keeps the Hindi-English mix intact, normalizes spelling variants, removes only leading discourse fillers.
- **Word packs** (`swarscribe packs`): export, import and share dictionaries and snippets as JSON; developer and Hinglish packs bundled.
- **One-click installers** (`packaging/`): PyInstaller spec and build scripts for Linux and Windows plus an Inno Setup installer script. The Linux single-file binary (26 MB) is built, smoke-tested and attached to this release.
- **System tray app** (`swarscribe tray`): tray icon with Dictate, Dashboard and Quit, via the desktop extra.
- **Chrome extension** (`extension/`): a mic button beside any web text field, cleanup running locally in the page.
- **VS Code and Obsidian integrations** (`integrations/`): clean selected dictation through the local CLI without leaving the editor.
- **Android floating bubble**: overlay mic bubble service with drag, tap-to-dictate and long-press to dismiss, plus the permission flow in the app.
- **Published benchmarks** (docs/BENCHMARKS.md): measured on a small shared CPU, faster-whisper tiny and base both scored WER 0.000 on the sample clip at 8.5x and 5.2x real time; cleanup about 63,000 words per second. Methodology and limits stated.
- 70 tests, all passing.

## v0.5.0, 2026-11-13

### Made to be found, and to be used
- **Live demo on GitHub Pages**: the web demo is served straight from this repo, linked at the top of the README. No install, no sign-up.
- **README rebuilt for people**: live CI, Android and release badges, who it is for, an FAQ that answers the privacy and cost questions honestly, Android APK download instructions, and a star call to action.
- **`swarscribe dict`**: teach the dictionary from the terminal (list, add, remove), verified end to end: a word taught in one command is applied by the next cleanup.
- **`swarscribe history`**: recent dictations, undo, and Markdown export from the terminal.
- **Hotkey mode**: `swarscribe app --hotkey` holds a global hotkey in any app, the original Wispr pattern, alongside the terminal mode.
- **Social preview card** in `assets/social-preview.svg`, set as the repo's sharing image, so links to SwarScribe look like SwarScribe everywhere.
- 54 tests, all passing.

## v0.4.0, 2026-11-13

### It actually dictates now
- **Real transcription, verified end to end:** faster-whisper was installed and the full path (audio file in, model, transcript, cleanup) transcribed the JFK sample perfectly, and the recorder path (AudioBuffer, VAD trim, WAV, transcribe) verified the same way. This is the first release where speech to text is proven, not just plumbed.
- **Desktop app** (`swarscribe app`): push-to-talk recording with the new `recorder.py`, energy based VAD in `vad.py` that trims silence before the model ever sees it, model registry and cache in `models.py`, local history and stats persisted in `~/.swarscribe`, clean text typed at the cursor.
- **Dashboard:** new API endpoints `/stats`, `/models`, `/dictionary` and `/transcribe`, a `web/dashboard.html` page that renders them, and `swarscribe dashboard` / `swarscribe models` commands.
- **Android app and keyboard** in `android/`: a companion app plus a system input method (one mic button, cleaned text committed at the cursor in any app), a Kotlin port of the cleanup rules, on-device recognition with the offline preference, and server mode, where the phone records and your own desktop transcribes over your Wi-Fi. An Android CI workflow builds the debug APK on every Android change.
- Dependency note: the whisper extra now pins `av<15`, because faster-whisper 1.2 calls a PyAV API that newer PyAV removed.
- 52 tests, all passing.

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
