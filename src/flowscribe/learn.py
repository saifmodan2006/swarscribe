"""Auto-learn: FlowScribe learns your words from your edits.

New in v0.2, and something Wispr Flow does not do: when you correct
the cleaned output by hand, FlowScribe compares the two versions,
finds the word swaps, and offers them as personal dictionary entries.
Correct "devbysafe" to "devbysaif" once, and it is right forever.
Nothing is learned silently into the live dictionary unless the
caller applies it, and the pairs are plain data you can inspect.
"""

from __future__ import annotations

import difflib
import re

from .dictionary import PersonalDictionary

_TOKEN = re.compile(r"[A-Za-z0-9@._-]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text)


def learn_from_edit(original: str, edited: str) -> list[tuple[str, str]]:
    """Return (heard, correct) word pairs from a user's hand edit.

    Only clean one-to-one word replacements are learned. Insertions,
    deletions and rewrites are ignored, so a heavy edit never teaches
    the dictionary nonsense.
    """
    a, b = _tokens(original), _tokens(edited)
    pairs: list[tuple[str, str]] = []
    matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "replace":
            continue
        if (i2 - i1) != (j2 - j1):
            continue
        for old, new in zip(a[i1:i2], b[j1:j2]):
            if old.lower() != new.lower() and len(new) > 1:
                pairs.append((old.lower(), new))
    return pairs


def apply_learning(dictionary: PersonalDictionary, original: str,
                   edited: str) -> list[tuple[str, str]]:
    """Learn from an edit straight into a dictionary. Returns pairs."""
    pairs = learn_from_edit(original, edited)
    for heard, correct in pairs:
        dictionary.add(heard, correct)
    return pairs
