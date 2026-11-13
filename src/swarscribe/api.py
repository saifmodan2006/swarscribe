"""FastAPI backend: SwarScribe as a service.

Run: uvicorn swarscribe.api:app --reload
Docs: http://127.0.0.1:8000/docs

Endpoints:
- POST /clean     {text, style?, app?, code_mode?} -> cleaned text
- POST /command   {text, command} -> edited text
- POST /code      {text} -> code-shaped text
- POST /meeting   {transcript} -> summary, decisions, action items
- GET  /health    -> status and version

FastAPI is an optional extra: pip install swarscribe[api]
"""

from __future__ import annotations

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
except ImportError:  # pragma: no cover
    FastAPI = None

from . import __version__
from .codemode import to_code
from .commands import apply_command
from .dictionary import PersonalDictionary
from .meeting import analyse_meeting
from .pipeline import Pipeline
from .snippets import SnippetLibrary

if FastAPI is not None:
    app = FastAPI(title="SwarScribe", version=__version__,
                  description="Offline-first AI dictation API")
    _pipeline = Pipeline(
        dictionary=PersonalDictionary.default_for_saif(),
        snippets=SnippetLibrary.defaults())

    class CleanIn(BaseModel):
        text: str
        style: str | None = None
        app: str | None = None
        code_mode: bool = False

    class CommandIn(BaseModel):
        text: str
        command: str

    class TextIn(BaseModel):
        text: str

    @app.get("/health")
    def health():
        return {"status": "ok", "version": __version__,
                "privacy": "local-first, no audio uploaded by default"}

    @app.post("/clean")
    def clean(payload: CleanIn):
        result = _pipeline.process(payload.text, style=payload.style,
                                   app=payload.app,
                                   code_mode=payload.code_mode)
        return {"raw": result.raw, "text": result.text,
                "stages": result.stages, "style": result.style}

    @app.post("/command")
    def command(payload: CommandIn):
        return {"text": apply_command(payload.text, payload.command)}

    @app.post("/code")
    def code(payload: TextIn):
        return {"text": to_code(payload.text)}

    @app.post("/meeting")
    def meeting(payload: TextIn):
        notes = analyse_meeting(payload.text)
        return {"summary": notes.summary,
                "decisions": notes.decisions,
                "action_items": notes.action_items,
                "markdown": notes.to_markdown()}
else:  # pragma: no cover
    app = None
