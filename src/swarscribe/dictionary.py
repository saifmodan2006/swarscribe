"""Personal dictionary: teach SwarScribe your words once.

Wispr Flow has a dictionary. SwarScribe goes further: the dictionary
is a plain, portable mapping you own, it preserves capitalisation,
and `suggest()` can flag likely mis-hearings of your terms in a raw
transcript so the list grows with use.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


def _is_word_character(character: str) -> bool:
    # Python's regex \w excludes combining marks such as Hindi vowel signs.
    return (character.isalnum() or character == "_"
            or unicodedata.category(character).startswith("M"))


@dataclass
class PersonalDictionary:
    entries: dict[str, str] = field(default_factory=dict)

    def add(self, heard: str, correct: str) -> None:
        self.entries[heard.lower()] = correct

    def remove(self, heard: str) -> None:
        self.entries.pop(heard.lower(), None)

    def apply(self, text: str) -> str:
        for heard, correct in self.entries.items():
            if not heard:
                continue
            pat = re.compile(re.escape(heard), flags=re.I)
            parts = []
            previous_end = search_start = 0
            while match := pat.search(text, search_start):
                start, end = match.span()
                if (start and _is_word_character(text[start - 1])) or (
                    end < len(text) and _is_word_character(text[end])
                ):
                    # A rejected phrase may overlap a later whole-word match.
                    search_start = start + 1
                    continue
                parts.extend((text[previous_end:start], correct))
                previous_end = search_start = end
            parts.append(text[previous_end:])
            text = "".join(parts)
        return text

    def suggest(self, text: str) -> list[str]:
        """Return dictionary terms that appear (in any case) in text."""
        found = []
        low = text.lower()
        for heard, correct in self.entries.items():
            if heard in low and correct not in text:
                found.append(correct)
        return found

    @classmethod
    def default_for_saif(cls) -> "PersonalDictionary":
        d = cls()
        for heard, correct in [
            ("safe modan", "Saif Modan"),
            ("dev by safe", "devbysaif"),
            ("devbysafe", "devbysaif"),
            ("fast a p i", "FastAPI"),
            ("rag", "RAG"),
            ("pie torch", "PyTorch"),
        ]:
            d.add(heard, correct)
        return d
