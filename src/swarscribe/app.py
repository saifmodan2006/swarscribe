"""Shared dictation processing and the interactive terminal workflow."""

from __future__ import annotations

from pathlib import Path
from threading import RLock

from .analytics import Analytics
from .config import Config
from .history import History
from .models import cache_dir
from .pipeline import Pipeline
from .recorder import Recorder
from .transcribe import transcribe_wav_bytes

state_lock = RLock()


def state_dir() -> Path:
    return cache_dir().parent


def build_pipeline(config: Config | None = None) -> tuple[Pipeline, History, Analytics]:
    config = config or Config.load()
    folder = state_dir()
    hist_path = folder / "history.json"
    stats_path = folder / "stats.json"
    history = History.load(hist_path) if hist_path.exists() else History()
    analytics = Analytics.load(stats_path) if stats_path.exists() else Analytics()
    history.prune(config.history_days)
    return config.pipeline(), history, analytics


def persist_result(raw: str, text: str, seconds: float, config: Config) -> None:
    with state_lock:
        current = Config.load()
        _, history, analytics = build_pipeline(current)
        folder = state_dir()
        if config.keep_history and current.keep_history:
            history.add(raw, text)
        if config.keep_history or (folder / "history.json").exists():
            history.save(folder / "history.json")
        analytics.record(text, seconds)
        analytics.save(folder / "stats.json")


def process_dictation(raw: str, config: Config, app: str | None = None) -> str:
    if config.mode == "meeting":
        from .meeting import analyse_meeting
        return analyse_meeting(raw).to_markdown()
    return config.pipeline().process(
        raw, app=app, style=config.style or config.app_styles.get(app or ""),
        code_mode=config.mode == "code", cleanup=config.mode == "smart").text


def dictate_once(recorder: Recorder, backend, pipe: Pipeline,
                 analytics: Analytics, prompt: bool = True) -> str:
    """Compatibility helper for callers using an injected pipeline."""
    if prompt:
        input("Press Enter and speak... ")
    recorder.start()
    try:
        if prompt:
            input("Press Enter when done. ")
    finally:
        buffer = recorder.stop()
    if buffer.silent():
        return ""
    transcript = transcribe_wav_bytes(buffer.wav_bytes(), backend)
    result = pipe.process(transcript.text)
    if result.text:
        analytics.record(result.text, buffer.seconds)
    return result.text


def run_app(engine: str | None = None, model: str | None = None,
            config: Config | None = None) -> None:
    config = config or Config.load()
    config.engine = engine or config.engine
    config.model = model or config.model
    if config.mode == "command":
        raise RuntimeError("Selection commands require the Windows global hotkey or tray.")
    backend = config.backend()
    recorder = Recorder(device=config.microphone)
    print("SwarScribe terminal dictation. Ctrl+C quits.")
    try:
        while True:
            input("Press Enter to record... ")
            recorder.start()
            try:
                input("Press Enter to stop... ")
            finally:
                buffer = recorder.stop()
            if buffer.silent():
                print("No speech detected.")
                continue
            heard = transcribe_wav_bytes(buffer.wav_bytes(), backend, config.language)
            text = process_dictation(heard.text, config) if heard.text else ""
            if text:
                persist_result(heard.text, text, buffer.seconds, config)
                print(text)
            else:
                print("No text recognized.")
    except (KeyboardInterrupt, EOFError):
        print("\nSession ended.")
