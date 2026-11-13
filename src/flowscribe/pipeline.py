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


@dataclass
class Result:
    raw: str
    text: str
    mode: str = "dictation"
    style: str | None = None
    stages: list[str] = field(default_factory=list)


class Pipeline:
    def __init__(self, dictionary: PersonalDictionary | None = None,
                 snippets: SnippetLibrary | None = None,
                 enhancer=None, analytics: Analytics | None = None):
        self.dictionary = dictionary or PersonalDictionary()
        self.snippets = snippets or SnippetLibrary()
        self.enhancer = enhancer
        self.analytics = analytics

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
        return Result(raw=raw, text=text, mode=mode,
                      style=chosen_style, stages=stages)
