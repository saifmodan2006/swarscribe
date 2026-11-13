"""Loopback dashboard/API and a separate, explicitly paired HTTPS speech service."""

from __future__ import annotations

import base64
import binascii
import io
import ipaddress
import logging
import secrets
import wave
from dataclasses import asdict
from pathlib import Path
from threading import BoundedSemaphore
from typing import Annotated, Literal
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import __version__
from .app import build_pipeline, persist_result, process_dictation, state_dir, state_lock
from .codemode import to_code
from .commands import apply_command
from .config import Config
from .meeting import analyse_meeting
from .models import status as model_status
from .transcribe import BackendUnavailable, TranscriptionError, transcribe_wav_bytes

MAX_AUDIO_BYTES = 6 * 1024 * 1024
MAX_AUDIO_SECONDS = 120
MAX_BODY = 4 * ((MAX_AUDIO_BYTES + 2) // 3) + 4096
DASHBOARD = Path(__file__).resolve().parent / "dashboard"
LOGGER = logging.getLogger(__name__)
Style = Literal["formal", "casual", "email", "chat", "document", "plain"]
Language = Annotated[str, StringConstraints(pattern=r"^(auto|hinglish|[a-z]{2,3})$")]
Key = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Value = Annotated[str, StringConstraints(min_length=1, max_length=2000)]


class Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TextIn(Body):
    text: str = Field(max_length=50_000)


class CleanIn(TextIn):
    style: Style | None = None
    app: str | None = Field(None, max_length=100)
    code_mode: bool = False


class CommandIn(TextIn):
    command: str = Field(max_length=160)


class TranscribeIn(Body):
    wav_base64: str = Field(min_length=1, max_length=MAX_BODY - 4096)
    language: Language | None = None


class EntriesIn(Body):
    entries: dict[Key, Value] = Field(max_length=1000)


class SettingsIn(Body):
    engine: Literal["auto", "whisper", "parakeet"]
    model: Literal["tiny", "base", "small", "medium", "large-v3", "large-v3-turbo"] | None = None
    device: Literal["auto", "cpu", "cuda"]
    language: Language | None
    mode: Literal["normal", "smart", "code", "command", "meeting"]
    style: Style | None
    hotkey: str = Field(min_length=1, max_length=60)
    toggle: bool
    local_only: bool
    keep_history: bool
    history_days: int = Field(ge=1, le=365)
    ollama_model: str | None = Field(None, max_length=120, pattern=r"^[a-zA-Z0-9._:/-]+$")


def error(status: int, message: str) -> JSONResponse:
    return JSONResponse({"detail": message}, status_code=status,
                        headers={"Cache-Control": "no-store"})


def loopback(value: str | None) -> bool:
    try:
        return bool(value and ipaddress.ip_address(value).is_loopback)
    except ValueError:
        return False


def wav_duration(audio: bytes) -> float:
    try:
        with wave.open(io.BytesIO(audio), "rb") as source:
            rate, frames = source.getframerate(), source.getnframes()
            if (source.getnchannels() != 1 or source.getsampwidth() != 2
                    or rate not in {8000, 16000, 22050, 24000, 32000, 44100, 48000}
                    or not frames):
                raise ValueError
            if frames > rate * MAX_AUDIO_SECONDS:
                raise HTTPException(413, "Audio exceeds the 120-second limit.")
            if len(source.readframes(frames)) != frames * 2:
                raise ValueError
            return frames / rate
    except (ValueError, wave.Error, EOFError) as exc:
        raise HTTPException(422, "Use a complete mono PCM16 WAV at a supported sample rate.") from exc


def create_app(*, lan_token: str | None = None, lan_hostname: str | None = None) -> FastAPI:
    paired = lan_token is not None
    if paired and (len(lan_token or "") < 32 or not lan_hostname):
        raise ValueError("LAN mode needs a hostname and a token of at least 32 characters.")
    api = FastAPI(title="SwarScribe", version=__version__,
                  docs_url=None if paired else "/docs",
                  redoc_url=None, openapi_url=None if paired else "/openapi.json")
    speech_slot = BoundedSemaphore(1)

    class BodyLimit:
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH"}:
                await self.app(scope, receive, send)
                return
            limit = MAX_BODY if scope["path"] == "/transcribe" else 512 * 1024
            data = bytearray()
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                chunk = message.get("body", b"")
                if len(chunk) + len(data) > limit:
                    await error(413, "Request body is too large.")(scope, receive, send)
                    return
                data.extend(chunk)
                if not message.get("more_body"):
                    break
            sent = False

            async def replay():
                nonlocal sent
                if sent:
                    return await receive()
                sent = True
                return {"type": "http.request", "body": bytes(data), "more_body": False}

            await self.app(scope, replay, send)

    api.add_middleware(BodyLimit)

    @api.middleware("http")
    async def protect(request: Request, call_next):
        host = request.headers.get("host", "")
        try:
            parsed = urlsplit(f"//{host}")
            hostname = parsed.hostname
            _ = parsed.port
            if parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
                return error(400, "Invalid Host header.")
        except ValueError:
            return error(400, "Invalid Host header.")

        origin = request.headers.get("origin")
        if paired:
            if request.url.scheme != "https" or hostname != lan_hostname:
                return error(403, "Use the configured HTTPS pairing address.")
            provided = request.headers.get("authorization", "").encode("utf-8")
            expected = f"Bearer {lan_token}".encode("utf-8")
            if not secrets.compare_digest(provided, expected):
                return error(401, "Pairing token required or incorrect.")
            if (request.method, request.url.path) not in {("GET", "/health"), ("POST", "/transcribe")}:
                return error(404, "Endpoint unavailable in pairing mode.")
        elif (hostname != "localhost" and not loopback(hostname)) or not loopback(
                request.client.host if request.client else None):
            return error(403, "The dashboard is available on loopback only.")

        if ((origin is not None and origin != f"{request.url.scheme}://{host}")
                or request.headers.get("sec-fetch-site") == "cross-site"):
            return error(403, "Cross-origin access is disabled.")
        if request.method in {"PUT", "PATCH", "DELETE"}:
            if request.headers.get("x-swarscribe-local") != "1":
                return error(403, "Local settings header required.")

        if request.method in {"POST", "PUT", "PATCH"}:
            if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
                return error(415, "Use application/json.")
            limit = MAX_BODY if request.url.path == "/transcribe" else 512 * 1024
            try:
                declared = int(request.headers.get("content-length", "0"))
            except ValueError:
                return error(400, "Invalid Content-Length.")
            if declared < 0 or declared > limit:
                return error(413, "Request body is too large.")
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @api.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return error(422, "Invalid request fields. Check the API schema and size limits.")

    @api.exception_handler(StarletteHTTPException)
    async def http_error(request, exc):
        return error(exc.status_code, str(exc.detail))

    @api.exception_handler(Exception)
    async def unexpected(request, exc):
        LOGGER.error("API operation failed: %s", type(exc).__name__)
        return error(500, "Local operation failed. Check the server configuration and storage.")

    @api.get("/", include_in_schema=False)
    def dashboard():
        return FileResponse(DASHBOARD / "index.html", headers={
            "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        })

    @api.get("/dashboard.js", include_in_schema=False)
    def dashboard_script():
        return FileResponse(DASHBOARD / "dashboard.js", media_type="text/javascript")

    @api.get("/dashboard.css", include_in_schema=False)
    def dashboard_style():
        return FileResponse(DASHBOARD / "dashboard.css", media_type="text/css")

    @api.get("/health")
    def health():
        return {"status": "ok", "version": __version__, "paired": paired}

    @api.post("/clean")
    def clean(payload: CleanIn):
        result = Config.load().pipeline().process(
            payload.text, style=payload.style, app=payload.app, code_mode=payload.code_mode)
        return asdict(result)

    @api.post("/command")
    def command(payload: CommandIn):
        return {"text": apply_command(payload.text, payload.command)}

    @api.post("/code")
    def code(payload: TextIn):
        return {"text": to_code(payload.text)}

    @api.post("/meeting")
    def meeting(payload: TextIn):
        notes = analyse_meeting(payload.text)
        return {"summary": notes.summary, "decisions": notes.decisions,
                "action_items": notes.action_items, "markdown": notes.to_markdown()}

    @api.get("/stats")
    def stats():
        _, _, analytics = build_pipeline()
        return analytics.summary()

    @api.get("/models")
    def models():
        return {"models": model_status()}

    @api.get("/settings")
    def settings():
        config = Config.load()
        return {name: getattr(config, name) for name in SettingsIn.model_fields}

    @api.put("/settings")
    def update_settings(payload: SettingsIn):
        from .desktop import parse_hotkey
        try:
            parse_hotkey(payload.hotkey)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        if payload.engine == "parakeet" and payload.model is not None:
            raise HTTPException(422, "Parakeet uses its own model. Clear the Whisper model override.")
        with state_lock:
            config = Config.load()
            for field, value in payload.model_dump().items():
                setattr(config, field, value)
            config.save()
            _, history, _ = build_pipeline(config)
            path = state_dir() / "history.json"
            if path.exists():
                history.save(path)
        return settings()

    @api.get("/dictionary")
    def dictionary():
        return {"entries": Config.load().dictionary}

    @api.put("/dictionary")
    def update_dictionary(payload: EntriesIn):
        with state_lock:
            config = Config.load()
            config.dictionary = {key.lower(): value for key, value in payload.entries.items()}
            config.save()
        return dictionary()

    @api.get("/snippets")
    def snippets():
        return {"entries": Config.load().snippets}

    @api.put("/snippets")
    def update_snippets(payload: EntriesIn):
        with state_lock:
            config = Config.load()
            config.snippets = {key.lower(): value for key, value in payload.entries.items()}
            config.save()
        return snippets()

    @api.get("/history")
    def history(q: Annotated[str, Query(max_length=200)] = ""):
        _, store, _ = build_pipeline()
        return {"entries": [{"id": entry.id, "text": entry.text, "timestamp": entry.timestamp}
                            for entry in reversed(store.entries) if q.casefold() in entry.text.casefold()][:200]}

    @api.get("/history/export")
    def export_history():
        _, store, _ = build_pipeline()
        return PlainTextResponse(store.export_markdown(),
                                 headers={"Content-Disposition": 'attachment; filename="swarscribe-history.md"'})

    @api.delete("/history")
    def clear_history():
        with state_lock:
            _, store, _ = build_pipeline()
            store.entries.clear()
            store.save(state_dir() / "history.json")
        return {"ok": True}

    @api.delete("/history/{entry_id}")
    def delete_history(entry_id: str):
        with state_lock:
            _, store, _ = build_pipeline()
            if not store.delete(entry_id):
                raise HTTPException(404, "History entry not found.")
            store.save(state_dir() / "history.json")
        return {"ok": True}

    @api.post("/transcribe")
    def transcribe(payload: TranscribeIn):
        try:
            audio = base64.b64decode(payload.wav_base64, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise HTTPException(422, "Audio must be valid base64.") from exc
        if len(audio) > MAX_AUDIO_BYTES:
            raise HTTPException(413, "Audio exceeds the 6 MiB upload limit.")
        seconds = wav_duration(audio)
        if not speech_slot.acquire(blocking=False):
            raise HTTPException(429, "The speech engine is busy. Try again shortly.")
        try:
            config = Config.load()
            config.language = payload.language or config.language
            heard = transcribe_wav_bytes(audio, config.backend(), config.language)
            if not heard.text.strip():
                raise HTTPException(422, "No speech was recognized.")
            if config.mode in {"command", "meeting"}:
                config.mode = "smart"
            text = process_dictation(heard.text, config)
            # Paired audio is transcribed without silently adding it to desktop history.
            if not paired and text:
                persist_result(heard.text, text, seconds, config)
            return {"raw": heard.text, "text": text, "engine": heard.engine,
                    "language": heard.language, "segments": [asdict(s) for s in heard.segments]}
        except BackendUnavailable as exc:
            raise HTTPException(503, str(exc) if not paired else
                                "Desktop speech model unavailable. Check desktop setup.") from exc
        except TranscriptionError as exc:
            raise HTTPException(422, str(exc)) from exc
        finally:
            speech_slot.release()

    return api


app = create_app()
