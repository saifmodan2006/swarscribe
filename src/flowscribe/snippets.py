"""Snippets: say a short trigger, insert a long block of text.

Examples: say "my portfolio" and get the full URL plus one-liner,
or "my signature" and get a complete email sign-off. Snippets are
checked after cleanup, so filler words in the trigger are forgiven.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class SnippetLibrary:
    snippets: dict[str, str] = field(default_factory=dict)

    def add(self, trigger: str, expansion: str) -> None:
        self.snippets[trigger.strip().lower()] = expansion

    def remove(self, trigger: str) -> None:
        self.snippets.pop(trigger.strip().lower(), None)

    def expand(self, text: str) -> str:
        out = text
        for trigger, expansion in self.snippets.items():
            pat = re.compile(rf"\b{re.escape(trigger)}\b\.?", flags=re.I)
            out = pat.sub(expansion, out)
        return out

    def triggers_in(self, text: str) -> list[str]:
        low = text.lower()
        return [t for t in self.snippets if t in low]

    @classmethod
    def defaults(cls) -> "SnippetLibrary":
        lib = cls()
        lib.add("my portfolio", "https://www.devbysaif.in/")
        lib.add("my github", "https://github.com/saifmodan2006")
        lib.add("my linkedin", "https://www.linkedin.com/in/saif-modan")
        lib.add("my signature",
                "Best regards,\nSaif Modan\nPython and AI Developer\n"
                "https://www.devbysaif.in/")
        return lib
