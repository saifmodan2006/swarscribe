"""The FlowScribe pipeline: raw speech in, finished text out.

Stages, in order:
1. Transcription (dual engine, see transcribe.py) or text-in
2. Smart cleanup (fillers, corrections, spoken punctuation, lists)
3. Personal dictionary
4. Snippets
5. Code mode, when the target is a code editor
6. Per-app style
7. Optional local LLM enhancement
8. Analytics recording

Every stage is optional, deterministic where it matters, and runs
on the user's machine by default.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .analytics import Analytics
from .cleanup import clean_text
from .codemode import to_code
from .dictionary import PersonalDictionary
from .snippets import SnippetLibrary
from .styles import apply_style, style_for_app


def _edit_stats(raw: str, text: str) -> dict:
    """How much work the pipeline just saved the user, in numbers."""
    import difflib
    a, b = raw.lower().split(), text.lower().split()
    matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    changed = sum(max(i2 - i1, j2 - j1)
                  for tag, i1, i2, j1, j2 in matcher.get_opcodes()
                  if tag != "equal")
    return {"raw_words": len(a), "clean_words": len(b),
            "edits_made": changed}


@dataclass
class Result:
    raw: str
    text: str
    mode: str = "dictation"
    style: str | None = None
    stages: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


class Pipeline:
    def __init__(self, dictionary: PersonalDictionary | None = None,
                 snippets: SnippetLibrary | None = None,
                 enhancer=None, analytics: Analytics | None = None,
                 history=None):
        self.dictionary = dictionary or PersonalDictionary()
        self.snippets = snippets or SnippetLibrary()
        self.enhancer = enhancer
        self.analytics = analytics
        self.history = history

    def learn(self, edited_text: str) -> list:
        """Auto-learn dictionary pairs from the user's edit of the
        most recent result (see learn.py). Returns learned pairs."""
        if self.history is None or not self.history.entries:
            return []
        from .learn import apply_learning
        last = self.history.entries[-1]
        return apply_learning(self.dictionary, last.text, edited_text)

    def process(self, raw: str, *, app: str | None = None,
                style: str | None = None, code_mode: bool = False,
                seconds: float | None = None) -> Result:
        stages = []
        text = clean_text(raw)
        stages.append("cleanup")
        if self.dictionary.entries:
            text = self.dictionary.apply(text)
            stages.append("dictionary")
        if self.snippets.snippets:
            text = self.snippets.expand(text)
            stages.append("snippets")
        mode = "dictation"
        if code_mode:
            text = to_code(text)
            mode = "code"
            stages.append("code-mode")
        chosen_style = style or style_for_app(app)
        if chosen_style:
            text = apply_style(text, chosen_style)
            stages.append(f"style:{chosen_style}")
        if self.enhancer is not None:
            text = self.enhancer.enhance(text)
            stages.append("llm")
        if self.analytics is not None and seconds:
            self.analytics.record(text, seconds)
            stages.append("analytics")
        if self.history is not None:
            self.history.add(raw, text)
            stages.append("history")
        return Result(raw=raw, text=text, mode=mode,
                      style=chosen_style, stages=stages,
                      stats=_edit_stats(raw, text))
