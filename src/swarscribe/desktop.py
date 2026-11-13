"""Windows dictation with one hotkey listener and one audio worker."""

from __future__ import annotations

import re
import sys
from queue import Empty, Queue
from threading import Event, Lock

from .app import persist_result, process_dictation
from .commands import KNOWN_COMMANDS, apply_command
from .config import Config
from .recorder import Recorder
from .transcribe import transcribe_wav_bytes

KEYS = {"ctrl", "alt", "shift", "win", "space", "tab", "enter", "pause"}
ALIASES = {"cmd": "win", "escape": "esc", "control": "ctrl"}


def parse_hotkey(value: str) -> frozenset[str]:
    keys = [ALIASES.get(key, key) for part in value.lower().split("+")
            for key in (part.strip().strip("<>"),)]
    if (not keys or len(keys) != len(set(keys))
            or not all(key in KEYS or re.fullmatch(r"[a-z0-9]|f(?:[1-9]|1[0-9]|2[0-4])", key)
                       for key in keys)):
        raise ValueError("Use a hotkey such as ctrl+win, ctrl+shift+d, or f9.")
    return frozenset(keys)


class HotkeyState:
    def __init__(self, hotkey: str, toggle: bool = False):
        self.keys = parse_hotkey(hotkey)
        self.toggle = toggle
        self.down: set[str] = set()
        self.active = False

    def update(self, key: str, pressed: bool) -> str | None:
        if key not in self.keys:
            return None
        before = self.keys <= self.down
        if pressed:
            self.down.add(key)
        else:
            self.down.discard(key)
        after = self.keys <= self.down
        if not before and after:
            self.active = not self.active if self.toggle else True
            return "start" if self.active else "stop"
        if before and not after and not self.toggle and self.active:
            self.active = False
            return "stop"
        return None


def paste_at_cursor(text: str) -> str:
    from .windows import foreground, send_text
    if sys.platform != "win32":
        return "Direct insertion is supported on Windows."
    return send_text(text, foreground())


def run_desktop(config: Config, *, shutdown: Event | None = None,
                on_status=print, reload_config=Config.load) -> None:
    if sys.platform != "win32":
        raise RuntimeError("Global hotkey dictation is supported on Windows. Use swarscribe app.")
    try:
        from pynput import keyboard
    except ImportError as exc:
        raise RuntimeError("Install 'swarscribe[desktop]' for Windows dictation.") from exc

    from .windows import Focus, foreground, send_text

    shutdown = shutdown or Event()
    hotkey = HotkeyState(config.hotkey, config.toggle)
    events: Queue = Queue(maxsize=4)
    cancel = Event()
    idle = Event()
    idle.set()
    guard = Lock()
    accepted = False
    last_edit = None

    def key_event(key, pressed, injected=False):
        nonlocal accepted
        if key is None or injected:
            return
        key = listener.canonical(key)
        name = key.char if isinstance(key, keyboard.KeyCode) else key.name
        if not name:
            return
        name = ALIASES.get(name.lower(), name.lower())
        if name == "esc" and pressed and not idle.is_set():
            cancel.set()
            return
        with guard:
            action = hotkey.update(name, pressed)
            if action == "start":
                accepted = idle.is_set()
                if accepted:
                    idle.clear()
                    cancel.clear()
                    events.put_nowait(("start", foreground()))
            elif action == "stop" and accepted:
                accepted = False
                events.put_nowait(("stop", None))

    def finish():
        nonlocal accepted
        with guard:
            accepted = False
            hotkey.active = False
            while not events.empty():
                events.get_nowait()
            idle.set()

    def command(heard, target, editor_id, selected, config):
        nonlocal last_edit
        import ctypes
        from ctypes import wintypes

        request = heard.lower().strip(" .!?")
        if foreground().hwnd != target.hwnd:
            return "Focus changed before the command could run."
        if request in {"undo", "undo the last transformation"}:
            if not last_edit or last_edit[:3] != (target.hwnd, editor_id, selected):
                return "Select the previous replacement in the same editor to undo it."
            replacement = last_edit[3]
        elif request in {"fix grammar", "rewrite professionally"}:
            if not config.ollama_model:
                return "Set a local Ollama model in dashboard settings to enable this rewrite."
            from .llm import rewrite_locally
            replacement = rewrite_locally(selected, request, config.ollama_model)
        elif all(part in KNOWN_COMMANDS for part in request.split(" and ")):
            replacement = apply_command(selected, request)
        else:
            return "Command unavailable. Try make it formal, shorten it, or convert to bullet points."
        if replacement == selected:
            return "No changes proposed."
        user = ctypes.windll.user32
        preview = replacement[:1000] + ("…" if len(replacement) > 1000 else "")
        approved = user.MessageBoxW(wintypes.HWND(target.hwnd),
                                    "Replace the current selection?\n\n" + preview,
                                    "SwarScribe Command Mode", 0x0004 | 0x0100)
        if approved != 6:
            return "Replacement cancelled."
        if cancel.is_set() or shutdown.is_set():
            return "Replacement cancelled."
        result = send_text(replacement, target, selected, editor_id)
        if result == "Text sent to the editor.":
            last_edit = (target.hwnd, editor_id, replacement, selected)
        return result

    def report(message):
        on_status(message)

    listener = keyboard.Listener(on_press=lambda key, injected=False: key_event(key, True, injected),
                                 on_release=lambda key, injected=False: key_event(key, False, injected))
    listener.start()
    report(f"Ready: {'tap to start/stop' if config.toggle else 'hold'} {config.hotkey}. Esc cancels.")
    try:
        while not shutdown.is_set() and listener.is_alive():
            try:
                action, target = events.get(timeout=0.1)
            except Empty:
                continue
            if action != "start":
                continue
            recorder = None
            try:
                current = reload_config()
                # Explicit launch overrides persist until restart.
                for key in getattr(config, "_overrides", ()):
                    setattr(current, key, getattr(config, key))
                with Focus() as focus:
                    if current.mode != "meeting" and not focus.writable():
                        raise RuntimeError("Focus a supported text editor first.")
                    editor_id = tuple(focus.element.GetRuntimeId())
                    selected = focus.selection() if current.mode == "command" else None
                if current.mode == "command" and (not selected or len(selected) > 8000):
                    raise RuntimeError("Select up to 8,000 characters in a supported editor first.")
                recorder = Recorder(device=current.microphone)
                recorder.start()
                report(f"Recording · {current.mode} · {current.language or 'auto'}")
                while not (shutdown.is_set() or cancel.is_set() or recorder.full):
                    try:
                        if events.get(timeout=0.1)[0] == "stop":
                            break
                    except Empty:
                        if not listener.is_alive():
                            cancel.set()
                buffer = recorder.stop()
                if shutdown.is_set() or cancel.is_set():
                    report("Recording cancelled.")
                    continue
                if recorder.overrun:
                    report("Microphone dropped audio. Try recording again.")
                    continue
                if buffer.silent():
                    report("No speech detected.")
                    continue
                report(f"Transcribing · {current.engine} / {current.model or 'default model'}")
                heard = transcribe_wav_bytes(buffer.wav_bytes(), current.backend(), current.language)
                if cancel.is_set() or shutdown.is_set():
                    report("Transcription discarded.")
                    continue
                if not heard.text:
                    report("No text recognized.")
                    continue
                if current.mode == "command":
                    report(command(heard.text, target, editor_id, selected, current))
                    continue
                text = process_dictation(heard.text, current, target.app)
                if not text:
                    report("No text after processing.")
                    continue
                persist_result(heard.text, text, buffer.seconds, current)
                if current.mode == "meeting":
                    report("Meeting notes saved in history." if current.keep_history else text)
                else:
                    report(send_text(text, target, editor_id=editor_id))
            except Exception as exc:
                report(f"Dictation error: {exc}")
            finally:
                try:
                    if recorder is not None:
                        recorder.stop()
                finally:
                    finish()
    finally:
        listener.stop()
        listener.join(timeout=1)
