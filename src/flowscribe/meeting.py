"""Meeting Mode: long dictation in, structured notes out.

Wispr added a separate Notetaker product. In FlowScribe it is the
same pipeline with a longer memory: dictate or paste a whole meeting
transcript and get a summary extract, decisions and action items,
with no meeting bot joining the call and nothing leaving the device.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

ACTION_CUES = ("will ", "need to", "needs to", "todo", "action:",
               "please ", "should ", "must ")
DECISION_CUES = ("decided", "agreed", "decision:", "we will go with",
                 "final:")


@dataclass
class MeetingNotes:
    summary: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        def section(title: str, items: list[str], bullet: str = "-") -> str:
            if not items:
                return f"## {title}\n\nNone captured.\n"
            body = "\n".join(f"{bullet} {i}" for i in items)
            return f"## {title}\n\n{body}\n"

        actions = [f"[ ] {i}" for i in self.action_items]
        return "\n".join([
            "# Meeting Notes", "",
            section("Summary", self.summary),
            section("Decisions", self.decisions),
            section("Action Items", actions),
        ])


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
    return [p.strip() for p in parts if p.strip()]


def analyse_meeting(transcript: str, summary_limit: int = 3) -> MeetingNotes:
    sentences = _sentences(transcript)
    notes = MeetingNotes()
    for s in sentences:
        low = s.lower()
        if any(cue in low for cue in DECISION_CUES):
            notes.decisions.append(s)
        elif any(cue in low for cue in ACTION_CUES):
            notes.action_items.append(s)
    # Summary = the longest, most content-rich remaining sentences,
    # kept in original order. Simple and deterministic offline.
    rest = [s for s in sentences
            if s not in notes.decisions and s not in notes.action_items]
    ranked = sorted(rest, key=lambda s: len(s.split()), reverse=True)
    chosen = ranked[:summary_limit]
    notes.summary = [s for s in rest if s in chosen]
    return notes
