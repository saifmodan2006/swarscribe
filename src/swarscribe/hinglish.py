"""Hinglish mode: cleanup tuned for mixed Hindi and English speech.

India talks in two languages at once, and generic dictation cleanup
mangles it. Hinglish mode keeps the mix intact: it removes only clear
discourse fillers, normalizes common Hinglish spellings that Whisper
hears inconsistently, and never translates or "corrects" Hindi words
into English. Use language hint "hi" for transcription, then run this
pass after the normal cleanup.
"""

from __future__ import annotations

import re

# Sentence-initial discourse fillers that carry no meaning in Hinglish
# dictation. Only removed at the start of a sentence, never mid-clause,
# where the same words can be real content.
_LEADING_FILLERS = ("matlab", "arre", "arey", "achha toh", "toh")

# Spelling variants Whisper produces for the same Hinglish words.
_VARIANTS = {
    "bahot": "bahut",
    "bohot": "bahut",
    "kaisa hai": "kaisa hai",
    "theek hai": "theek hai",
    "bilkul sahi": "bilkul sahi",
}


def clean_hinglish(text: str) -> str:
    out = text
    for heard, fixed in _VARIANTS.items():
        def _swap(match, fixed=fixed):
            word = match.group(0)
            return fixed[:1].upper() + fixed[1:] \
                if word[:1].isupper() else fixed
        out = re.sub(rf"\b{re.escape(heard)}\b", _swap, out,
                     flags=re.IGNORECASE)
    sentences = re.split(r"(?<=[.!?])\s+", out)
    cleaned = []
    for sentence in sentences:
        lowered = sentence.lower()
        for filler in _LEADING_FILLERS:
            if lowered.startswith(filler + " "):
                sentence = sentence[len(filler) + 1:]
                sentence = sentence[:1].upper() + sentence[1:]
                break
        cleaned.append(sentence)
    return " ".join(cleaned).strip()
