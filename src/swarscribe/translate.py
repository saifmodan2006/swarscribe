"""Translation mode: speak one language, land another.

New in v0.2. Two layers, honest about which one is working:

1. Phrasebook (offline, built in): common greetings and work phrases
   between English and Hindi, in both directions. Small and exact.
2. LLM layer (optional): pass any enhancer with an `enhance` method
   and a translation instruction, for full sentences. Local Ollama
   keeps it private, the same rule as the rest of SwarScribe.

If neither layer knows the text, the original is returned unchanged.
SwarScribe never invents a translation.
"""

from __future__ import annotations

PHRASEBOOK: dict[tuple[str, str], dict[str, str]] = {
    ("en", "hi"): {
        "hello": "नमस्ते",
        "thank you": "धन्यवाद",
        "good morning": "शुभ प्रभात",
        "please send the file": "कृपया फ़ाइल भेजें",
        "the meeting is tomorrow": "मीटिंग कल है",
        "i will call you": "मैं आपको कॉल करूँगा",
    },
    ("hi", "en"): {},
}
for (_src, _dst), _table in list(PHRASEBOOK.items()):
    if _src == "en":
        PHRASEBOOK[("hi", "en")] = {v: k for k, v in _table.items()}


def translate_text(text: str, source: str, target: str,
                   enhancer=None) -> str:
    if not text or source == target:
        return text
    table = PHRASEBOOK.get((source, target), {})
    hit = table.get(text.strip().lower().rstrip("."))
    if hit:
        return hit
    if enhancer is not None:
        prompt = (f"Translate the following text from {source} to "
                  f"{target}. Return only the translation.\n\n{text}")
        out = enhancer.enhance(prompt)
        if out and out != prompt:
            return out
    return text
