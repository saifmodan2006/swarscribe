"""Command Mode: edit existing text with your voice.

Select text anywhere, then speak an instruction instead of typing
the edit. Wispr Flow charges for this on its Pro plan. In FlowScribe
it is built in and works offline for the core commands:

- "make it formal" / "make it casual"
- "make it shorter" (drops intensifiers and filler adjectives)
- "make it a list" / "bullet list"
- "uppercase" / "lowercase" / "title case"
- "add a greeting" / "sign off" for quick email shaping
- "remove fillers" (re-runs the cleanup filler pass)
"""

from __future__ import annotations

import re

from .cleanup import _remove_fillers
from .styles import apply_style

INTENSIFIERS = ["very", "really", "just", "actually", "basically",
                "literally", "simply", "quite"]


def _shorten(text: str) -> str:
    out = text
    for word in INTENSIFIERS:
        out = re.sub(rf"\b{word}\b\s*", "", out, flags=re.I)
    out = re.sub(r"\s{2,}", " ", out).strip()
    out = re.sub(r"\s+([,.!?])", r"\1", out)
    if out:
        out = out[0].upper() + out[1:]
    return out


def _bullet_list(text: str) -> str:
    body = text.strip().rstrip(".")
    parts = re.split(r",\s*|\s+and\s+", body)
    items = [p.strip() for p in parts if p.strip()]
    return "\n".join(f"- {item}" for item in items)


def apply_command(text: str, command: str) -> str:
    """Apply a spoken editing command to text. Unknown commands are
    returned unchanged so a mis-heard command never destroys text."""
    if not text:
        return text
    cmd = command.strip().lower().rstrip(".")
    if cmd in ("make it formal", "make formal", "formal"):
        return apply_style(text, "formal")
    if cmd in ("make it casual", "make casual", "casual"):
        return apply_style(text, "casual")
    if cmd in ("make it shorter", "shorten it", "shorten", "make shorter"):
        return _shorten(text)
    if cmd in ("make it a list", "make a list", "bullet list",
               "turn it into a list"):
        return _bullet_list(text)
    if cmd == "uppercase":
        return text.upper()
    if cmd == "lowercase":
        return text.lower()
    if cmd == "title case":
        return text.title()
    if cmd in ("remove fillers", "clean it up", "clean up"):
        cleaned = _remove_fillers(text)
        return re.sub(r"\s{2,}", " ", cleaned).strip()
    if cmd == "add a greeting":
        return "Hello,\n\n" + text
    if cmd in ("sign off", "add sign off", "add a sign off"):
        return text.rstrip() + "\n\nBest regards"
    return text
