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
from .streaming import iter_file_events


@dataclass
class TimedSegment:
    start_seconds: float
    text: str
    timing: str = "model"


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
        lines = [f"# {self.title}", "", "## Extractive summary", "",
                 self.summary or "No summary available.", ""]
        if self.decisions:
            lines += ["## Decisions", ""]
            lines += [f"- {item}" for item in self.decisions] + [""]
        if self.actions:
            lines += ["## Action items", ""]
            lines += [f"- [ ] {item}" for item in self.actions] + [""]
        lines += ["## Transcript", "",
                  "Times mark model segments or, where labeled, the start of an audio chunk.", ""]
        for segment in self.segments:
            stamp = f"{int(segment.start_seconds // 60):02d}:" \
                    f"{int(segment.start_seconds % 60):02d}"
            label = " (chunk)" if segment.timing == "chunk" else ""
            lines.append(f"**[{stamp}]{label}** {segment.text}")
        return "\n".join(lines) + "\n"


def record_meeting_notes(wav_path: str, transcribe_wav,
                         title: str = "Meeting notes") -> MeetingNote:
    """Transcribe a recording into a structured, timestamped note."""
    events = iter_file_events(wav_path, transcribe_wav, chunk_ms=100)
    segments: list[TimedSegment] = []
    for event in events:
        if event.kind != "final":
            continue
        segments.append(TimedSegment(event.start_seconds, event.text, event.timing))
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
    with path.open("x", encoding="utf-8") as output:
        output.write(note.to_markdown())
    return path


def capture_meeting(wav_path: str, device=None) -> None:
    """Record to disk with consent and avoid overwriting recordings."""
    import queue
    import threading
    import wave

    try:
        import sounddevice as sd
    except ImportError as exc:
        raise RuntimeError("Install the desktop extra to record meetings.") from exc
    path = Path(wav_path)
    rate = int(sd.query_devices(device, "input")["default_samplerate"])
    blocks = queue.Queue(maxsize=32)
    lost = threading.Event()
    stopped = threading.Event()
    input("Press Enter to start recording. Make sure everyone has consented. ")

    def callback(data, frames, time, status):
        try:
            if status:
                lost.set()
            blocks.put_nowait(bytes(data))
        except queue.Full:
            lost.set()

    def wait_for_stop():
        try:
            input("Recording. Press Enter to stop. ")
        except EOFError:
            pass
        finally:
            stopped.set()

    with path.open("xb") as file, wave.open(file, "wb") as output:
        output.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        with sd.RawInputStream(device=device, samplerate=rate, channels=1, dtype="int16",
                               callback=callback, blocksize=rate // 10):
            threading.Thread(target=wait_for_stop, daemon=True).start()
            while not stopped.is_set() and not lost.is_set():
                try:
                    output.writeframesraw(blocks.get(timeout=0.1))
                except queue.Empty:
                    continue
        while not blocks.empty():
            output.writeframesraw(blocks.get_nowait())
    if lost.is_set():
        raise RuntimeError("Microphone interrupted. Partial recording was saved.")
