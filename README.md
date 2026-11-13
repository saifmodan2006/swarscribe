# SwarScribe

![SwarScribe banner](assets/banner.svg)

**Speak naturally. Get finished text. Nothing leaves your device.**

SwarScribe is an offline-first AI dictation system that does the job of Wispr Flow, and then keeps going: dual-engine transcription, smart cleanup, voice command editing, a dedicated code mode, meeting notes, and dictation analytics, all built from open source, all free, with no word caps and no account.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Privacy](https://img.shields.io/badge/privacy-local%20first-brightgreen)
[![Release](https://img.shields.io/github/v/release/saifmodan2006/swarscribe)](https://github.com/saifmodan2006/swarscribe/releases)
[![CI](https://github.com/saifmodan2006/swarscribe/actions/workflows/ci.yml/badge.svg)](https://github.com/saifmodan2006/swarscribe/actions/workflows/ci.yml)
[![Android](https://github.com/saifmodan2006/swarscribe/actions/workflows/android.yml/badge.svg)](https://github.com/saifmodan2006/swarscribe/actions/workflows/android.yml)
![Tests](https://img.shields.io/badge/tests-54%20passing-brightgreen)

**[Try the live demo in your browser](https://saifmodan2006.github.io/swarscribe/web/)** · No install, no sign-up, nothing uploaded. If SwarScribe saves you typing, a star helps the next person find it.

> Wispr Flow sends every word you say to the cloud, caps its free plan at 2,000 words a week, and charges for Command Mode. SwarScribe runs on your machine, has no caps, and treats those features as table stakes.

## What it does

Hold a hotkey, speak the way you actually talk, rambling, fillers, mid-sentence corrections and all, and SwarScribe lands clean, formatted text wherever your cursor is.

```text
You say:   um the meeting is on monday no wait tuesday at five comma
           and uh please check my portfolio

You get:   The meeting is on Tuesday at five, and please check
           https://www.devbysaif.in/
```

## Features that go beyond Wispr Flow

| Feature | What it means |
| --- | --- |
| **Dual-engine transcription** | NVIDIA Parakeet v3 for fast English dictation, Whisper large-v3-turbo for 99 languages. Picked automatically by language. |
| **Offline first, private by design** | Audio, transcripts, dictionary and history never leave your machine unless you turn on a cloud option yourself. Wispr is cloud only. |
| **No word caps, no subscription** | Dictate all day. It is MIT licensed open source. |
| **Smart cleanup** | Fillers removed, stutters fixed, self-corrections resolved ("on Monday, no wait, Tuesday" keeps only Tuesday), spoken punctuation and lists formatted. |
| **Command Mode, built in** | Select text and say "make it formal", "make it shorter", "make it a list". Free, not a Pro upsell. |
| **Code Mode** | Dictate real code: "snake case user name equals five" becomes `user_name = 5`. CamelCase, PascalCase, symbols and digits included. |
| **Per-app styles** | Formal in email, casual in chat, clean in documents, applied automatically by the app you are dictating into. |
| **Personal dictionary that learns the shape of your life** | Your names, projects and jargon, in a plain file you own, with mis-hearing suggestions. |
| **Snippets** | Say "my portfolio" or "my signature", get the full block. |
| **Meeting Mode** | Dictate or paste a whole meeting, get a summary, decisions and action items. No bot joins your call. |
| **Hinglish ready** | Whisper language routing plus cleanup tuned for mixed Hindi and English speech, the way India actually talks. |
| **Dictation analytics** | Words dictated, speaking speed, and an honest estimate of minutes saved versus typing at 40 WPM. Stored locally, for you only. |
| **Smart formats (v0.2)** | Emails, websites, times, dates and amounts land written: "five thirty pm" becomes 5:30 PM, "fifteen november 2026" becomes 15 November 2026, "saif modan at gmail dot com" becomes saifmodan@gmail.com. |
| **Auto-learn (v0.2)** | Correct a word by hand once and SwarScribe learns it into your dictionary. Wispr makes you add words manually. |
| **Command chains (v0.2)** | Voice macros in one breath: "make it formal and shorten it" runs both edits, in order. |
| **Translation mode (v0.2)** | Speak English, land Hindi, or the other way, with an offline phrasebook and an optional local LLM layer for full sentences. |
| **History and edit stats (v0.2)** | Undo for dictation sessions, Markdown export, and every result reports how many edits the pipeline just saved you. |
| **API and web demo included** | A FastAPI service and a zero-backend browser demo ship in the repo. |

## What is new in v0.5

Made for people, not just for tests: a live browser demo on GitHub Pages, a proper README with badges that reflect the real build status, `swarscribe dict` commands so teaching it your words takes one line, `swarscribe history` with undo and Markdown export from the terminal, a global hotkey mode for the desktop app, and a social preview card so the project looks like itself when shared. See [CHANGELOG.md](CHANGELOG.md).

## Who it is for

- **Writers and professionals** who think faster than they type and want emails and documents at speaking speed, privately.
- **Developers** who want to dictate code, commit messages and docs without a cloud service listening.
- **Students and researchers** turning lectures and voice notes into clean notes and meeting summaries.
- **Anyone who cannot type comfortably** for long, for any reason. Voice first is an accessibility feature, not a luxury.
- **Multilingual speakers**, especially Hinglish speakers, who mix languages the way people actually talk.

## Android app

The `android/` project builds a real APK in CI on every change: open the [Android workflow](https://github.com/saifmodan2006/swarscribe/actions/workflows/android.yml), pick the latest green run, and download the `swarscribe-debug-apk` artifact. Install it, enable the SwarScribe keyboard once, and dictate into any app. Details: [android/README.md](android/README.md).

## FAQ

**Is it really free?** Yes. MIT licensed, no accounts, no word caps, no premium tier. The speech models are open source too.

**Is my voice uploaded anywhere?** No. Desktop transcription runs on your machine. The web demo uses your browser's own speech support if you allow the mic, and the cleanup runs in the page. Android server mode sends audio only to your own desktop on your own Wi-Fi.

**Which languages?** Whisper covers 99 languages including Hindi. Parakeet covers English and 25 European languages, faster. Hinglish gets a language hint plus cleanup tuned for mixed speech.

**Windows, Mac, Linux?** The Python app and CLI run anywhere Python 3.10+ runs. The Android app needs Android 8 or newer. iOS is on the roadmap.

**How is this different from Wispr Flow?** Wispr is polished and cloud based, with a subscription and word caps on the free plan. SwarScribe is local, free, open source, and adds Code Mode, Meeting Mode, smart formats and an auto-learning dictionary. Wispr still wins on hosted polish and its iPhone app today; the honest comparison is in [docs/COMPARISON.md](docs/COMPARISON.md).

## Performance

The cleanup pipeline is the hot path, so it is precompiled, allocation-light standard library Python with no model calls and no I/O. Run the honest, on-your-machine numbers yourself:

```bash
python benchmarks/benchmark.py
```

Full side-by-side: [docs/COMPARISON.md](docs/COMPARISON.md)

## Quick start

No model download is needed to try the cleanup pipeline, the demo, the CLI text commands, the API, or the web demo.

```bash
git clone https://github.com/saifmodan2006/swarscribe.git
cd swarscribe
pip install -e .

# Clean raw dictation text
swarscribe clean "um the meeting is on monday no wait tuesday at five"

# Voice-edit text
swarscribe command --do "make it formal" --text "i can't make it"

# Dictate code
swarscribe code "snake case user name equals five"

# Meeting notes from a transcript file
swarscribe meeting examples/sample_transcript.txt

# See it all working
python examples/demo.py
```

Add real speech transcription when you are ready:

```bash
pip install -e ".[whisper]"     # Whisper large-v3-turbo, 99 languages
pip install -e ".[parakeet]"    # NVIDIA Parakeet v3, fastest English
pip install -e ".[api]"         # FastAPI service
pip install -e ".[desktop]"     # push-to-talk + paste at cursor

swarscribe transcribe recording.wav --language en
uvicorn swarscribe.api:app --reload   # API docs at /docs
```

For the web demo, just open `web/index.html` in a browser. It runs the cleanup pipeline in JavaScript, supports mic input where the browser allows it, and needs no server.

## How it works

```text
mic / audio / text in
  -> transcription (Parakeet for speed, Whisper for languages)
  -> cleanup (fillers, corrections, punctuation, lists)
  -> personal dictionary -> snippets
  -> code mode (optional) -> per-app style
  -> optional local LLM pass (Ollama, on your machine)
  -> typed at your cursor, or returned by the API
  -> local analytics
```

Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · Roadmap: [docs/ROADMAP.md](docs/ROADMAP.md)

## Project layout

```text
src/swarscribe/   the package: pipeline, cleanup, transcribe, codemode,
                  commands, meeting, analytics, desktop, api, cli
web/              zero-backend browser demo
docs/             architecture, Wispr comparison, roadmap
examples/         runnable demo and a sample meeting transcript
tests/            unit tests for every core feature (stdlib unittest,
                  also runs under pytest)
```

## Tests

```bash
python -m unittest discover -s tests -v
# or
pytest
```

## Built with open source

- [NVIDIA Parakeet](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) and [NeMo](https://github.com/NVIDIA/NeMo)
- [OpenAI Whisper](https://github.com/openai/whisper) (MIT) via [faster-whisper](https://github.com/SYSTRAN/faster-whisper) and whisper.cpp
- [FastAPI](https://fastapi.tiangolo.com/), [Ollama](https://ollama.com/) for the optional local LLM pass
- Inspired by the open source dictation community: [Handy](https://github.com/cjpais/Handy) and [OpenWhispr](https://github.com/OpenWhispr/openwhispr), both MIT, proved local system-wide dictation works

SwarScribe is an original implementation. It does not use Wispr Flow code, models, or branding beyond naming it as the reference product it improves on.

## Contributing

Issues and pull requests are welcome. Keep PRs small, tested, and focused, one feature or fix at a time.

## Author

**Saif Modan** · Python and AI Developer · Ahmedabad, India
Portfolio: [devbysaif.in](https://www.devbysaif.in/) · LinkedIn: [saif-modan](https://www.linkedin.com/in/saif-modan) · GitHub: [@saifmodan2006](https://github.com/saifmodan2006)

## License

MIT. See [LICENSE](LICENSE).
