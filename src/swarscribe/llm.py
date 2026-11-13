"""Optional LLM enhancement, local first.

The rule pipeline is the default and always works offline. When the
user wants a deeper rewrite, SwarScribe can pass cleaned text to a
local LLM through Ollama (no data leaves the machine), or to any
OpenAI-compatible endpoint the user configures with their own key.
If the LLM is unreachable, SwarScribe silently keeps the rule output.
Your dictation never depends on a server being up.
"""

from __future__ import annotations

import json
import urllib.request

SYSTEM_PROMPT = (
    "You rewrite dictated text into clean written text. Remove filler "
    "words, apply self-corrections, fix grammar and punctuation, and "
    "format lists as lists. Do not add new content. Do not summarise. "
    "Return only the rewritten text."
)

COMMAND_PROMPTS = {
    "fix grammar": "Correct grammar and punctuation while preserving the meaning and language.",
    "rewrite professionally": "Rewrite in a professional tone without changing meaning or adding facts.",
}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def rewrite_locally(text: str, command: str, model: str) -> str:
    """Opt-in selected-text rewriting through Ollama on loopback, with no fallback."""
    payload = json.dumps({
        "model": model, "stream": False,
        "options": {"num_predict": 2048},
        "messages": [
            {"role": "system", "content": COMMAND_PROMPTS[command] + " Return only the revised text."},
            {"role": "user", "content": text},
        ],
    }).encode()
    request = urllib.request.Request("http://127.0.0.1:11434/api/chat", data=payload,
                                     headers={"Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=60) as response:
            data = json.loads(response.read(131072))
        if data.get("done_reason") == "length":
            raise ValueError("Truncated rewrite.")
        rewritten = data["message"]["content"].strip()
        if not rewritten or len(rewritten) > 16000:
            raise ValueError("Empty or oversized rewrite.")
        return rewritten
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise RuntimeError("Ollama did not return a usable rewrite. Check the running local service and model.") from exc


class OllamaEnhancer:
    def __init__(self, model: str = "llama3.1:8b",
                 host: str = "http://localhost:11434", timeout: float = 20.0):
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout

    def enhance(self, text: str) -> str:
        payload = json.dumps({
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        }).encode()
        req = urllib.request.Request(
            self.host + "/api/chat", data=payload,
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read())
            out = data.get("message", {}).get("content", "").strip()
            return out or text
        except Exception:
            return text


class OpenAICompatibleEnhancer:
    """Works with any OpenAI-compatible chat endpoint the user picks."""

    def __init__(self, base_url: str, model: str, api_key: str,
                 timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def enhance(self, text: str) -> str:
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        }).encode()
        req = urllib.request.Request(
            self.base_url + "/chat/completions", data=payload,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.api_key}"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read())
            out = (data["choices"][0]["message"]["content"] or "").strip()
            return out or text
        except Exception:
            return text
