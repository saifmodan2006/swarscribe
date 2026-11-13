# SwarScribe

SwarScribe is an offline-first dictation project for Windows, Android, and the command line. It includes a local dashboard and a [browser demo](https://saifmodan2006.github.io/swarscribe/web/). The project is **alpha**.

## Quick start

On 64-bit Windows with Python 3.10–3.12, run in PowerShell from the cloned repository:

```powershell
py -3.12 -m venv .venv
$py = ".\.venv\Scripts\python.exe"
$ss = ".\.venv\Scripts\swarscribe.exe"
& $py -m pip install -e ".[whisper,desktop,api,dev]"
& $ss clean "um the meeting is on monday no wait tuesday"
& $ss model-download --engine whisper --model base
& $ss transcribe C:\path\to\speech.wav --engine whisper --model base --local-only
& $ss devices
& $ss tray
```

Hold **Ctrl+Win** to record, then release either key in the chord to transcribe. **Esc** discards the current result. Open the tray dashboard to select a mode, language, model, device, or toggle hotkey. Restart the tray after editing the hotkey. Prefer a combination that the target app does not use. To use a chosen microphone, run `swarscribe app --hotkey --microphone 1` with the index from `swarscribe devices`. `swarscribe app` is the terminal workflow and prints output. See [Windows setup and troubleshooting](docs/WINDOWS.md).

Run `swarscribe dashboard` and open the printed URL (default `http://127.0.0.1:8000/`). The dashboard serves its own assets and exposes local usage, history search/delete/export, dictionary, snippets and preferences. Stats count dictations with text and estimate time saved against a 40 WPM baseline. They do not measure whether a target application accepted insertion.

## Features and limits

| Feature | Implemented | Verification | Limitations |
|---|---|---|---|
| Whisper file and API transcription | Yes, faster-whisper | Real cached CPU inference in Linux/WSL, automated error and persistence checks | Windows native DLL loading may be blocked by application policy; CUDA is unverified |
| Parakeet | NeMo TDT v3 adapter | Backend routing and unsupported language tests | Requires a NeMo-compatible environment; model inference is not verified here |
| English, Hindi and mixed speech | Whisper language hints or auto detection | English real audio; mixed-script cleanup regression | Hinglish is best effort, with no automatic translation |
| Windows dictation | Tray and console hotkey; toggle; microphone selection; guarded Unicode insertion | Hotkey state tests and live microphone capture | Requires an editable Windows UI Automation control; app compatibility and end-to-end hotkey dictation need device tests |
| Smart cleanup and Code Mode | Shared Python pipeline | Python, JavaScript, SQL, formatting and dictionary cases | Spoken formatting rules can change meaning; Normal Mode skips prose cleanup |
| Voice commands | Selection preview, rule edits, explicit undo, optional local Ollama rewrites | Rule tests | UI Automation TextPattern support required; Ollama and real selection replacement need testing |
| Meetings | Microphone recording to WAV or WAV import; Markdown with actual audio offsets | Segment offset and note tests | Extractive highlights and keyword cues; no diarization or generative summaries |
| History, dictionary, snippets, analytics | Dashboard and CLI backed by local JSON | Persistence, settings, export, deletion and API tests | History retention applies on reads and is written on dictation or settings save; usage totals are separate |
| Local/paired API | Loopback dashboard; separate HTTPS + bearer token for speech | Authorization and upload validation tests | Requires a certificate trusted by the Android device and a matching host name |
| Android | On-device IME and companion; desktop mode in companion | Unit tests, lint, debug and unsigned release builds | No attached device; requires Android 12+ and offline speech service for on-device recognition |
| Web demo | Browser text cleanup and optional microphone | JavaScript format tests | Browser speech may use a remote vendor; no model is bundled in the demo |
| Translation | Limited English/Hindi phrasebook | Unit tests | Unknown phrases are returned unchanged; no general translation model wired into the CLI |

## Offline models and data

- Whisper defaults to multilingual `base` on CPU. Choose `tiny` for a smaller download, or a larger model for potential accuracy gains. Set **Use cached models only** in the dashboard or pass `--local-only` after the initial download. Use `--device cuda` only after meeting the [faster-whisper runtime requirements](https://github.com/SYSTRAN/faster-whisper#gpu). `--language hi` hints Hindi; `--language hinglish` uses Whisper auto detection without translating.
- Install `.[parakeet]` in a compatible Linux/NeMo environment and select `--engine parakeet`. For a cached offline checkpoint, supply a local `.nemo` file with `--model` and pass `--local-only`. Auto uses Whisper by default; explicitly selecting English without a model override can try Parakeet first and fall back to Whisper if initialization fails. An explicit engine never silently falls back.
- Desktop settings and data live in `~/.swarscribe` or `SWARSCRIBE_HOME`. History is on by default; turn off **Save new transcripts** or clear saved transcripts in the dashboard. Audio is normally temporary. Meeting capture saves an audio file only when invoked explicitly. See [security and privacy](SECURITY.md).
- Android on-device speech uses the system offline service. The paired companion sends audio to the HTTPS desktop address you provide. Optional [hosted bots](bots/README.md) receive content through their messaging providers and are separate from local dictation.

## Common commands

```powershell
swarscribe dict add "Super Base" Supabase
swarscribe packs export my-words my-words.json
swarscribe packs import my-words.json
swarscribe code "function definition add open parenthesis x close parenthesis colon new line indent return x plus two"
swarscribe command --do "convert to bullet points" --text "apples, pears and bananas"
swarscribe translate "thank you" --from-lang en --to-lang hi
swarscribe transcribe .\speech.wav --chunks --engine whisper --local-only
swarscribe meeting-record .\meeting.wav --out .\meeting-notes.md
swarscribe meeting-record .\new-meeting.wav --record --out .\new-notes.md
swarscribe history --search meeting
swarscribe history --export
```

`--chunks` emits partial/final JSON Lines from mono PCM16 WAV. Previews re-run local inference on a bounded audio chunk; finals are stable, but cuts can lose context. This is useful for file replay and integration. The Windows tray transcribes after recording stops. Meeting export uses model timestamps when present and labels audio chunk starts otherwise.

## Build and test

```powershell
& $py -m pip check
& $py -m pytest -q
& $py -m ruff check src tests --select E9,F63,F7,F82
node --test web/format.test.cjs
& $py -m build
& $py -m pip install pyinstaller pillow
& $py -m PyInstaller packaging/swarscribe.spec --noconfirm
.\dist\swarscribe.exe clean "um hello world"
gradle -p android testDebugUnitTest lintDebug assembleDebug assembleRelease assembleDebugAndroidTest
```

The PyInstaller artifact is a text CLI. Use the Python installation for speech, dashboard, and tray. The Android Gradle build requires JDK 17, Gradle 8.9 and Android SDK 34. See [Android setup](android/README.md) for pairing and APK paths. The browser demo is plain HTML/CSS/JS, served from `web/` with shared assets at `assets/`. Run `python -m http.server 8080` at the repo root and open `/web/`.

[Architecture](docs/ARCHITECTURE.md) · [Changelog](CHANGELOG.md) · [Contributing](CONTRIBUTING.md) · [MIT license](LICENSE)
