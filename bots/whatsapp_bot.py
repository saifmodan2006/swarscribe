"""SwarScribe WhatsApp voice-note bot (Meta Cloud API webhook).

Send a WhatsApp voice note to your number, get clean text back. The
webhook parsing is pure and tested; media download and reply sending go
through the official Cloud API with your own token.

Setup: create a Meta app with WhatsApp, point the webhook at
POST /whatsapp on a running SwarScribe API host, set the env vars
SWARSCRIBE_WA_VERIFY_TOKEN and SWARSCRIBE_WA_ACCESS_TOKEN, and mount
the router:  app.include_router(create_router(...))  (see bots/README).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def parse_message_event(payload: dict) -> dict | None:
    """Pull the first inbound message out of a Cloud API webhook body."""
    try:
        value = payload["entry"][0]["changes"][0]["value"]
        message = value["messages"][0]
    except (KeyError, IndexError, TypeError):
        return None
    kind = message.get("type")
    event = {"from": message.get("from"), "kind": kind}
    if kind == "audio":
        event["media_id"] = (message.get("audio") or {}).get("id")
    elif kind == "text":
        event["text"] = (message.get("text") or {}).get("body", "")
    return event


def verify_challenge(params: dict, expected_token: str) -> str | None:
    if (params.get("hub.mode") == "subscribe"
            and params.get("hub.verify_token") == expected_token):
        return params.get("hub.challenge")
    return None


def build_reply(event: dict, pipeline, transcribe_media) -> str | None:
    """transcribe_media(media_id) -> raw transcript text (injected)."""
    if event["kind"] == "audio" and event.get("media_id"):
        raw = transcribe_media(event["media_id"])
        return pipeline.process(raw).text
    if event["kind"] == "text" and event.get("text"):
        return pipeline.process(event["text"]).text
    return None


def create_router(pipeline, transcribe_media, sender):  # pragma: no cover
    """FastAPI router for the webhook. sender(to, text) sends a reply."""
    from fastapi import APIRouter, Request

    router = APIRouter()
    verify_token = os.environ.get("SWARSCRIBE_WA_VERIFY_TOKEN", "")

    @router.get("/whatsapp")
    async def verify(request: Request):
        challenge = verify_challenge(dict(request.query_params),
                                     verify_token)
        from fastapi.responses import PlainTextResponse
        if challenge is None:
            return PlainTextResponse("forbidden", status_code=403)
        return PlainTextResponse(challenge)

    @router.post("/whatsapp")
    async def receive(request: Request):
        event = parse_message_event(await request.json())
        if event:
            reply = build_reply(event, pipeline, transcribe_media)
            if reply:
                sender(event["from"], reply)
        return {"ok": True}

    return router
