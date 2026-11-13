"""Meeting recorder: a WAV in, timestamped notes out.

Takes a meeting recording (mic capture, call recording, voice memo),
streams it through the segmenter so long files stay cheap, transcribes
each segment locally, and writes a Markdown note: timestamped
transcript, summary, decisions and action items. Speaker labels are
only added if the caller supplies them per segment; SwarScribe does
not guess who spoke.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .meeting import analyse_meeting
from .streaming import stream_file


@dataclass
class TimedSegment:
    start_seconds: float
    text: str


@dataclass
class MeetingNote:
    title: str
    segments: list[TimedSegment] = field(default_factory=list)
    summary: str = ""
    decisions: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)

    @property
    def transcript(self) -> str:
        return " ".join(segment.text for segment in self.segments)

    def to_markdown(self) -> str:
        lines = [f"# {self.title}", "", "## Summary", "",
                 self.summary or "No summary available.", ""]
        if self.decisions:
            lines += ["## Decisions", ""]
            lines += [f"- {item}" for item in self.decisions] + [""]
        if self.actions:
            lines += ["## Action items", ""]
            lines += [f"- [ ] {item}" for item in self.actions] + [""]
        lines += ["## Transcript", ""]
        for segment in self.segments:
            stamp = f"{int(segment.start_seconds // 60):02d}:" \
                    f"{int(segment.start_seconds % 60):02d}"
            lines.append(f"**[{stamp}]** {segment.text}")
        return "\n".join(lines) + "\n"


def record_meeting_notes(wav_path: str, transcribe_wav,
                         title: str = "Meeting notes") -> MeetingNote:
    """Transcribe a recording into a structured, timestamped note."""
    events = stream_file(wav_path, transcribe_wav, chunk_ms=250)
    segments: list[TimedSegment] = []
    # Segment starts are estimated from word count at a typical speaking
    # pace (about 150 words per minute). They order the transcript and
    # help scanning; they are not sample-accurate timings.
    position = 0.0
    for event in events:
        if event.kind != "final":
            continue
        segments.append(TimedSegment(position, event.text))
        position += max(2.0, len(event.text.split()) / 2.5)
    joined = " ".join(segment.text for segment in segments)
    notes = analyse_meeting(joined) if joined else None
    return MeetingNote(
        title=title, segments=segments,
        summary=" ".join(notes.summary) if notes else "",
        decisions=notes.decisions if notes else [],
        actions=notes.action_items if notes else [])


def save_meeting_notes(wav_path: str, transcribe_wav, out_path: str,
                       title: str = "Meeting notes") -> Path:
    note = record_meeting_notes(wav_path, transcribe_wav, title=title)
    path = Path(out_path)
    path.write_text(note.to_markdown())
    return path
