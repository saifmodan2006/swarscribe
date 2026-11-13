"""Run: python examples/demo.py

Shows the whole FlowScribe pipeline on sample dictation, with no
model downloads and no network. This is text-in mode (EchoBackend):
in real use the raw text comes from Parakeet or Whisper.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from flowscribe import Pipeline
from flowscribe.analytics import Analytics
from flowscribe.commands import apply_command
from flowscribe.dictionary import PersonalDictionary
from flowscribe.meeting import analyse_meeting
from flowscribe.snippets import SnippetLibrary

pipe = Pipeline(dictionary=PersonalDictionary.default_for_saif(),
                snippets=SnippetLibrary.defaults(),
                analytics=Analytics())

samples = [
    "um the meeting is on monday no wait tuesday at five comma "
    "and uh please check my portfolio",
    "hi team comma i can't ship today period the build is broken",
    "first apples second bananas third oranges",
]
for raw in samples:
    result = pipe.process(raw, seconds=8)
    print("RAW :", raw)
    print("OUT :", result.text)
    print("VIA :", " -> ".join(result.stages))
    print()

print("COMMAND:", apply_command("I can't make it tomorrow.",
                                "make it formal"))
print("STATS  :", pipe.analytics.summary())

notes = analyse_meeting(
    "We discussed the roadmap in detail today. We decided to ship "
    "offline first. Rahul will prepare the demo by Friday. "
    "Priya needs to review the docs before release.")
print()
print(notes.to_markdown())
