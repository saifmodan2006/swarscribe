"""Smart cleanup: turn raw spoken rambling into written text.

This is the heart of FlowScribe. Wispr Flow cleans dictation in the
cloud. FlowScribe does it locally with a fast rule pipeline, and can
optionally pass the result through a local LLM (see llm.py) for a
deeper rewrite. The rule pipeline alone handles:

- filler words (um, uh, er, hmm, you know)
- stutter / word repetition (the the, I I I)
- self-corrections ("on Monday, no wait, Tuesday" keeps only Tuesday)
- spoken punctuation ("comma", "question mark", "new paragraph")
- number words in simple contexts (five -> 5 is left to code mode;
  cleanup keeps prose natural, see codemode.py)
- sentence capitalisation and spacing
- spoken list structure ("first ... second ... third ...")
"""

from __future__ import annotations

import re

FILLERS = [
    r"um+",
    r"uh+",
    r"er+",
    r"hmm+",
    r"mm+ hmm+",
]
FILLER_PHRASES = ["you know", "i mean like"]

# Order matters: multi-word phrases before single words.
SPOKEN_PUNCTUATION = [
    ("new paragraph", "\n\n"),
    ("new line", "\n"),
    ("question mark", "?"),
    ("exclamation mark", "!"),
    ("exclamation point", "!"),
    ("full stop", "."),
    ("period", "."),
    ("comma", ","),
    ("colon", ":"),
    ("semicolon", ";"),
    ("open parenthesis", "("),
    ("close parenthesis", ")"),
    ("open bracket", "["),
    ("close bracket", "]"),
    ("dash", " - "),
]

WEEKDAYS = {"monday", "tuesday", "wednesday", "thursday", "friday",
            "saturday", "sunday"}
MONTHS = {"january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december"}


def _remove_fillers(text: str) -> str:
    for phrase in FILLER_PHRASES:
        text = re.sub(rf"\b{phrase}\b,?", "", text, flags=re.I)
    for filler in FILLERS:
        text = re.sub(rf"\b{filler}\b,?", "", text, flags=re.I)
    return text


def _remove_repetitions(text: str) -> str:
    # "the the" -> "the", "I I I" -> "I" (immediate repeats only)
    return re.sub(r"\b(\w+)(\s+\1\b)+", r"\1", text, flags=re.I)


def _smart_title(word: str) -> str:
    if word.lower() in WEEKDAYS or word.lower() in MONTHS:
        return word.capitalize()
    return word


MARKER_PAIRS = [("no", "wait"), ("no", "sorry"), ("wait", "no")]


def _bare(word: str) -> str:
    return word.strip(",;:").lower()


def _apply_self_corrections(text: str) -> str:
    """Resolve "X, no wait, Y" style corrections, keeping Y.

      "on monday no wait tuesday at five" -> "on Tuesday at five"
      "at five, no wait, at six pm"       -> "at six pm"

    Rule: if the word after the marker repeats an anchor word just
    before it ("at ... at ..."), the whole anchored phrase is swapped
    for a phrase of the same length. Otherwise a single word is
    swapped for a single word.
    """
    tokens = text.replace(",", " , ").split()
    changed = True
    while changed:
        changed = False
        for i in range(len(tokens) - 1):
            pair = (_bare(tokens[i]), _bare(tokens[i + 1]))
            if pair not in MARKER_PAIRS:
                continue
            before = [t for t in tokens[:i] if t != ","]
            after = [t for t in tokens[i + 2:] if t != ","]
            if not before or not after:
                tokens = before + after
                changed = True
                break
            anchor_at = None
            for j in range(max(0, len(before) - 4), len(before)):
                if _bare(before[j]) == _bare(after[0]):
                    anchor_at = j
            if anchor_at is not None and len(before) - anchor_at > 1:
                span = len(before) - anchor_at
                tokens = before[:anchor_at] + after[:span] + after[span:]
            else:
                tokens = before[:-1] + after[:1] + after[1:]
            changed = True
            break
    return " ".join(tokens)


def _capitalise_calendar_words(text: str) -> str:
    for name in WEEKDAYS | MONTHS:
        text = re.sub(rf"\b{name}\b", name.capitalize(), text, flags=re.I)
    return text


def _apply_spoken_punctuation(text: str) -> str:
    lower_map = {}
    for phrase, symbol in SPOKEN_PUNCTUATION:
        lower_map[phrase] = symbol
        text = re.sub(rf"\s*\b{re.escape(phrase)}\b\s*", symbol + " ",
                      text, flags=re.I)
    # Tidy spaces around punctuation and collapse blank runs.
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _capitalise_sentences(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for part in parts:
        part = part.strip()
        if part:
            part = part[0].upper() + part[1:]
        out.append(part)
    text = " ".join(out)
    # Capitalise the start of each paragraph too.
    text = re.sub(r"\n(\w)", lambda m: "\n" + m.group(1).upper(), text)
    # Standalone "i" -> "I"
    text = re.sub(r"\bi\b", "I", text)
    return text


def _ensure_terminal_punctuation(text: str) -> str:
    if text and text[-1].isalnum():
        return text + "."
    return text


def _format_spoken_list(text: str) -> str:
    """Turn "first apples second bananas third oranges" into a list.

    Only triggers when all three markers appear, to avoid mangling
    ordinary prose that happens to use the word "first".
    """
    pat = re.compile(
        r"\bfirst\s+(.+?)\s+second\s+(.+?)\s+third\s+(.+)$", re.I | re.S)
    m = pat.search(text)
    if not m:
        return text
    items = [g.strip().rstrip(".") for g in m.groups()]
    lead = text[:m.start()].strip()
    bullets = "\n".join(f"- {item}" for item in items)
    return (lead + "\n" + bullets).strip() if lead else bullets


def clean_text(raw: str, *, use_list_format: bool = True) -> str:
    """Run the full rule cleanup pipeline on raw dictation text."""
    if not raw or not raw.strip():
        return ""
    text = " ".join(raw.split()) if "\n" not in raw else raw.strip()
    text = _apply_self_corrections(text)
    text = _remove_fillers(text)
    text = _remove_repetitions(text)
    text = _apply_spoken_punctuation(text)
    text = _capitalise_calendar_words(text)
    if use_list_format:
        text = _format_spoken_list(text)
    text = _capitalise_sentences(text)
    if "\n" not in text:
        text = _ensure_terminal_punctuation(text)
    return text.strip()
