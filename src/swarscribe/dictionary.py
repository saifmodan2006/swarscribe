"""Personal dictionary: teach SwarScribe your words once.

Wispr Flow has a dictionary. SwarScribe goes further: the dictionary
is a plain, portable mapping you own, it preserves capitalisation,
and `suggest()` can flag likely mis-hearings of your terms in a raw
transcript so the list grows with use.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class PersonalDictionary:
    entries: dict[str, str] = field(default_factory=dict)

    def add(self, heard: str, correct: str) -> None:
        self.entries[heard.lower()] = correct

    def remove(self, heard: str) -> None:
        self.entries.pop(heard.lower(), None)

    def apply(self, text: str) -> str:
        for heard, correct in self.entries.items():
            pat = re.compile(rf"\b{re.escape(heard)}\b", flags=re.I)

            def repl(m: re.Match, correct: str = correct) -> str:
                return correct

            text = pat.sub(repl, text)
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
