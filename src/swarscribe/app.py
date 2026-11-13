"""The SwarScribe desktop app: hold, speak, release, written.

Two ways to run it:

- Terminal mode (works anywhere): run `swarscribe app`, press Enter
  to start talking, Enter again to stop. Clean text is printed and
  copied, and typed at the cursor when the desktop extras allow it.
- Hotkey mode (desktop extras installed): hold the configured hotkey
  in any app, exactly like Wispr Flow.

Everything runs locally: the recorder feeds the VAD, the VAD trims
silence, the local model transcribes, and the cleanup pipeline does
the rest. Your history and stats stay in ~/.swarscribe.
"""
from __future__ import annotations

from pathlib import Path

from .analytics import Analytics
from .history import History
from .models import cache_dir
from .pipeline import Pipeline
from .recorder import Recorder
from .transcribe import choose_backend, transcribe_wav_bytes


def state_dir() -> Path:
    return cache_dir().parent


def build_pipeline() -> tuple[Pipeline, History, Analytics]:
    folder = state_dir()
    folder.mkdir(parents=True, exist_ok=True)
    history = History()
    hist_path = folder / "history.json"
    if hist_path.exists():
        history = History.load(hist_path)
    analytics = Analytics()
    stats_path = folder / "stats.json"
    if stats_path.exists():
        analytics = Analytics.load(stats_path)
    pipe = Pipeline(history=history)
    return pipe, history, analytics


def dictate_once(recorder: Recorder, backend, pipe: Pipeline,
                 analytics: Analytics, prompt: bool = True) -> str:
    """One full dictation: record, trim, transcribe, clean, record stats."""
    if prompt:
        input("Press Enter and speak... ")
    recorder.start()
    if prompt:
        input("Press Enter when done. ")
    buffer = recorder.stop()
    if buffer.silent():
        return ""
    transcript = transcribe_wav_bytes(buffer.wav_bytes(), backend)
    result = pipe.process(transcript.text)
    analytics.record(result.text, buffer.seconds)
    return result.text


def run_app(engine: str = "auto", model: str | None = None) -> None:
    from .desktop import paste_at_cursor
    pipe, history, analytics = build_pipeline()
    backend = choose_backend(engine, model=model)
    recorder = Recorder()
    print("SwarScribe is listening. Your voice never leaves this machine.")
    print("Ctrl+C quits. Each dictation is saved to your local history.")
    try:
        while True:
            text = dictate_once(recorder, backend, pipe, analytics)
            if not text:
                print("(silence, nothing written)")
                continue
            print("->", text)
            paste_at_cursor(text + " ")
            folder = state_dir()
            history.save(folder / "history.json")
            analytics.save(folder / "stats.json")
    except KeyboardInterrupt:
        summary = analytics.summary()
        print("\nSession over.", summary)
