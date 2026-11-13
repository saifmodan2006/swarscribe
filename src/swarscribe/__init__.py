"""SwarScribe: offline-first AI dictation that out-thinks Wispr Flow.

Speak naturally. Get clean, formatted, ready-to-paste text.
Dual-engine transcription (NVIDIA Parakeet for speed, Whisper for
99 languages), smart cleanup, voice command editing, code mode,
meeting notes, translation mode and dictation analytics.
100 percent private by default: everything can run on your machine.
"""

__version__ = "0.5.0"
__all__ = ["Pipeline", "clean_text", "__version__"]

from .pipeline import Pipeline
from .cleanup import clean_text
