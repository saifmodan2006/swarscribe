"""Smart formats: things people say that should land written.

New in v0.2. General dictation tools leave these as words. FlowScribe
recognises the shapes and writes them the way a person would type:

- emails:   "saif modan at gmail dot com"     -> saifmodan@gmail.com
            (a name before "at" is joined, the way mailboxes work)
- websites: "devbysaif dot in"                -> devbysaif.in
- times:    "five thirty pm"                  -> 5:30 PM
            "five pm"                         -> 5 PM
- dates:    "fifteen november 2026"           -> 15 November 2026
- amounts:  "five hundred rupees"             -> 500 rupees
            (number words are only converted in amount and time
            contexts, so prose like "one of us" is never mangled)
"""

from __future__ import annotations

import re

ONES = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19,
}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
        "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
MONTH_NAMES = ("january february march april may june july august "
               "september october november december").split()
TLDS = ("com", "in", "io", "org", "net", "dev", "ai", "co")
CURRENCIES = ("rupees", "dollars", "euros", "pounds")


def parse_number_words(words: list[str]) -> int | None:
    """Parse a small English number phrase, or return None.

    Supports 0 to 9999 shapes: "five", "twenty one",
    "five hundred", "five hundred fifty", "two thousand".
    """
    if not words:
        return None
    total, current, used = 0, 0, False
    for w in words:
        if w in ONES:
            current += ONES[w]
            used = True
        elif w in TENS:
            current += TENS[w]
            used = True
        elif w == "hundred":
            current = max(current, 1) * 100
            used = True
        elif w == "thousand":
            total += max(current, 1) * 1000
            current = 0
            used = True
        elif w == "and":
            continue
        else:
            return None
    return total + current if used else None


_EMAIL_STOP = r"(?:is|the|my|email|address|send|please|and|to)"


def _emails(text: str) -> str:
    # The tempered token stops the local part swallowing the words
    # before the name: "my email is saif modan at gmail dot com"
    # must yield saifmodan@, not emailissaifmodan@.
    pat = re.compile(
        rf"\b((?:(?!{_EMAIL_STOP}\s)\w+\s+){{0,3}}"
        rf"(?!{_EMAIL_STOP}\b)\w+)\s+at\s+((?:\w+\s+){{0,2}}\w+)\s+dot\s+"
        r"(" + "|".join(TLDS) + r")\b",
        flags=re.I)

    def repl(m: re.Match) -> str:
        local = "".join(m.group(1).lower().split())
        domain = "".join(m.group(2).lower().split())
        return f"{local}@{domain}.{m.group(3).lower()}"

    return pat.sub(repl, text)


def _websites(text: str) -> str:
    pat = re.compile(
        r"\b(\w+)\s+dot\s+(" + "|".join(TLDS) + r")\b", flags=re.I)
    return pat.sub(lambda m: f"{m.group(1).lower()}.{m.group(2).lower()}",
                   text)


def _times(text: str) -> str:
    hour_alt = "|".join(list(ONES.keys())[:13])  # zero..twelve

    def half_repl(m: re.Match) -> str:
        hour = ONES[m.group(1).lower()]
        minute = parse_number_words(m.group(2).lower().split()) or 0
        return f"{hour}:{minute:02d} {m.group(3).upper()}"

    text = re.sub(
        rf"\b({hour_alt})\s+((?:twenty|thirty|forty|fifty)(?:\s+"
        rf"(?:one|two|three|four|five|six|seven|eight|nine))?|"
        rf"(?:one|two|three|four|five|six|seven|eight|nine|ten|"
        rf"eleven|twelve|fifteen))\s+(am|pm)\b",
        half_repl, text, flags=re.I)
    text = re.sub(
        rf"\b({hour_alt})\s+(am|pm)\b",
        lambda m: f"{ONES[m.group(1).lower()]} {m.group(2).upper()}",
        text, flags=re.I)
    return text


def _dates(text: str) -> str:
    num_alt = "|".join(sorted(set(ONES) | set(TENS), key=len, reverse=True))
    month_alt = "|".join(MONTH_NAMES)
    pat = re.compile(
        rf"\b({num_alt}(?:\s+(?:{'|'.join(TENS)}))?)\s+({month_alt})\b"
        rf"(?:\s+(\d{{4}}))?",
        flags=re.I)

    def repl(m: re.Match) -> str:
        value = parse_number_words(m.group(1).lower().split())
        if value is None or value > 31:
            return m.group(0)
        out = f"{value} {m.group(2).capitalize()}"
        return out + (f" {m.group(3)}" if m.group(3) else "")

    return pat.sub(repl, text)


def _amounts(text: str) -> str:
    num_alt = "|".join(sorted(set(ONES) | set(TENS) | {"hundred", "thousand"},
                              key=len, reverse=True))
    curr_alt = "|".join(CURRENCIES)
    pat = re.compile(
        rf"\b((?:{num_alt})(?:\s+(?:{num_alt}|and)){{0,3}})\s+({curr_alt})\b",
        flags=re.I)

    def repl(m: re.Match) -> str:
        value = parse_number_words(m.group(1).lower().split())
        if value is None:
            return m.group(0)
        return f"{value} {m.group(2).lower()}"

    return pat.sub(repl, text)


def apply_smart_formats(text: str) -> str:
    if not text:
        return text
    out = _emails(text)
    out = _websites(out)
    out = _times(out)
    out = _dates(out)
    out = _amounts(out)
    return out
