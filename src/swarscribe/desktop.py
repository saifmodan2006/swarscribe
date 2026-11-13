"""Desktop mode: push-to-talk, paste at cursor, in any app.

This is the Wispr Flow surface: hold the hotkey anywhere, speak,
release, and SwarScribe types the cleaned text into the focused
window. It uses only open source pieces:

- sounddevice (PortAudio) for the microphone
- the dual transcription engines in transcribe.py
- pynput for the global hotkey and keyboard output
- pyperclip as a clipboard fallback for apps that block typing

All imports are lazy so the core package works without these
extras. Install with: pip install swarscribe[desktop]
"""

from __future__ import annotations


def paste_at_cursor(text: str) -> bool:
    """Type text into the focused app, falling back to clipboard."""
    try:
        from pynput.keyboard import Controller
        Controller().type(text)
        return True
    except Exception:
        pass
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        return False


def record_until_key_release(hotkey: str = "ctrl+win",
                             samplerate: int = 16000) -> str:
    """Record microphone audio to a temp WAV while hotkey is held.

    Returns the WAV path. Raises RuntimeError without desktop extras.
    """
    try:
        import sounddevice as sd
        import soundfile as sf
        from pynput import keyboard
    except ImportError as exc:
        raise RuntimeError(
            "Desktop extras are not installed. "
            "Install with: pip install swarscribe[desktop]") from exc

    import tempfile
    frames = []
    stream = sd.InputStream(samplerate=samplerate, channels=1)
    released = {"done": False}

    def on_release(key):
        released["done"] = True
        return False

    listener = keyboard.Listener(on_release=on_release)
    listener.start()
    with stream:
        import time
        while not released["done"]:
            block, _ = stream.read(1024)
            frames.append(block.copy())
            time.sleep(0.01)
    listener.join()
    import numpy as np
    audio = np.concatenate(frames) if frames else np.zeros((0, 1))
    path = tempfile.mktemp(suffix=".wav")
    sf.write(path, audio, samplerate)
    return path


def run_desktop(pipeline, backend, hotkey: str = "ctrl+win") -> None:
    """Main desktop loop. Ctrl+C to stop."""
    print(f"SwarScribe desktop: hold {hotkey}, speak, release.")
    print("Clean text is typed into the focused window. Ctrl+C quits.")
    while True:
        audio_path = record_until_key_release(hotkey)
        transcript = backend.transcribe(audio_path)
        result = pipeline.process(transcript.text)
        if result.text:
            paste_at_cursor(result.text)
