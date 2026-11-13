"""SwarScribe Telegram voice-note bot.

Send the bot a voice note, get clean formatted text back. Runs on the
same local pipeline as everything else: download the voice file from
Telegram, convert to WAV with ffmpeg, transcribe locally, clean, reply.

Setup (5 minutes, free):
  1. Talk to @BotFather on Telegram, create a bot, copy the token.
  2. pip install "swarscribe[whisper]"
  3. SWARSCRIBE_TELEGRAM_TOKEN=... python bots/telegram_bot.py

No database, no stored audio: files are deleted right after the reply.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from swarscribe.pipeline import Pipeline
from swarscribe.transcribe import choose_backend, transcribe_file

API = "https://api.telegram.org/bot{token}/{method}"


class TelegramAPI:
    def __init__(self, token: str):
        self.token = token

    def call(self, method: str, **params):
        data = json.dumps(params).encode()
        request = urllib.request.Request(
            API.format(token=self.token, method=method), data=data,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read())

    def download(self, file_id: str) -> bytes:
        info = self.call("getFile", file_id=file_id)
        path = info["result"]["file_path"]
        url = f"https://api.telegram.org/file/bot{self.token}/{path}"
        with urllib.request.urlopen(url, timeout=60) as response:
            return response.read()


def convert_to_wav(data: bytes, suffix: str = ".ogg") -> bytes:
    """Telegram voice notes are Opus in OGG; Whisper wants a real file."""
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / f"in{suffix}"
        dst = Path(tmp) / "out.wav"
        src.write_bytes(data)
        subprocess.run(["ffmpeg", "-y", "-i", str(src), "-ar", "16000",
                        "-ac", "1", str(dst)],
                       check=True, capture_output=True)
        return dst.read_bytes()


class VoiceNoteBot:
    def __init__(self, api: TelegramAPI, pipeline: Pipeline, backend,
                 downloader=None, converter=convert_to_wav):
        self.api = api
        self.pipeline = pipeline
        self.backend = backend
        self._download = downloader or api.download
        self._convert = converter

    def handle_update(self, update: dict) -> str | None:
        """Process one update; returns the reply text (or None to skip)."""
        message = update.get("message") or {}
        chat_id = (message.get("chat") or {}).get("id")
        if chat_id is None:
            return None
        voice = message.get("voice") or message.get("audio")
        if message.get("text", "").startswith("/start"):
            reply = ("Say it. It is written. Send me a voice note and I "
                     "will send back clean, formatted text. Hindi and "
                     "English both work. Nothing is stored.")
        elif voice:
            reply = self._handle_voice(voice["file_id"])
        elif message.get("text"):
            result = self.pipeline.process(message["text"])
            reply = result.text
        else:
            return None
        self.api.call("sendMessage", chat_id=chat_id, text=reply)
        return reply

    def _handle_voice(self, file_id: str) -> str:
        data = self._convert(self._download(file_id))
        with tempfile.NamedTemporaryFile(suffix=".wav",
                                         delete=False) as handle:
            handle.write(data)
            path = handle.name
        try:
            transcript = transcribe_file(path, backend=self.backend)
            result = self.pipeline.process(transcript.text)
            return result.text or "I could not hear anything in that note."
        finally:
            os.unlink(path)


def main():  # pragma: no cover - network loop
    token = os.environ["SWARSCRIBE_TELEGRAM_TOKEN"]
    api = TelegramAPI(token)
    model = os.environ.get("SWARSCRIBE_MODEL", "base")
    try:
        from swarscribe.transcribe import FasterWhisperBackend
        backend = FasterWhisperBackend(model=model)
    except Exception:
        backend = choose_backend("auto")
    bot = VoiceNoteBot(api, Pipeline(), backend)
    offset = 0
    print("SwarScribe bot listening. Send it a voice note.")
    while True:
        updates = api.call("getUpdates", offset=offset, timeout=50)
        for update in updates.get("result", []):
            offset = update["update_id"] + 1
            try:
                bot.handle_update(update)
            except Exception as error:  # keep the bot alive
                print("update failed:", error)


if __name__ == "__main__":
    main()
