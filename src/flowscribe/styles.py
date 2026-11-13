"""Per-app writing styles.

The same spoken sentence should land differently in an email and in
a chat. FlowScribe ships deterministic style transforms that work
offline with no LLM, and the pipeline can hand off to an LLM style
pass when one is configured.

Styles: formal, casual, email, chat, document.
"""

from __future__ import annotations

import re

EXPANSIONS = {
    "can't": "cannot", "won't": "will not", "don't": "do not",
    "doesn't": "does not", "didn't": "did not", "isn't": "is not",
    "aren't": "are not", "i'm": "I am", "you're": "you are",
    "we're": "we are", "it's": "it is", "that's": "that is",
    "let's": "let us", "i'll": "I will", "you'll": "you will",
    "we'll": "we will", "i've": "I have", "gonna": "going to",
    "wanna": "want to", "kinda": "kind of", "yeah": "yes",
}
CONTRACTIONS = {v: k for k, v in EXPANSIONS.items()
                 if v not in ("kind of", "yes")}


def _swap(text: str, mapping: dict[str, str]) -> str:
    for src, dst in mapping.items():
        pat = re.compile(rf"\b{re.escape(src)}\b", flags=re.I)

        def repl(m: re.Match, dst: str = dst) -> str:
            if m.group(0)[:1].isupper() and dst[:1].islower():
                return dst.capitalize()
            return dst

        text = pat.sub(repl, text)
    return text


def apply_style(text: str, style: str | None) -> str:
    if not text or not style:
        return text
    style = style.lower()
    if style in ("formal", "document"):
        return re.sub(r"\bi\b", "I", _swap(text, EXPANSIONS))
    if style in ("casual", "chat"):
        return _swap(text, CONTRACTIONS)
    if style == "email":
        out = _swap(text, EXPANSIONS)
        out = re.sub(r"^(hi|hey)\b", "Hello", out, flags=re.I)
        return out
    return text


APP_STYLE_MAP = {
    "gmail": "email", "outlook": "email", "mail": "email",
    "slack": "chat", "whatsapp": "chat", "telegram": "chat",
    "discord": "chat", "word": "document", "docs": "document",
    "notion": "document", "code": "document", "cursor": "document",
}


def style_for_app(app_name: str | None) -> str | None:
    if not app_name:
        return None
    return APP_STYLE_MAP.get(app_name.strip().lower())
