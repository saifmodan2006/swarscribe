"""Code Mode: dictate code without fighting the dictation engine.

Wispr Flow formats prose. FlowScribe also speaks developer:
- "snake case user name"        -> user_name
- "camel case user name"        -> userName
- "pascal case user profile"    -> UserProfile
- "constant case max retries"   -> MAX_RETRIES
- spoken symbols: open parenthesis, equals, arrow, colon, and more
- number words become digits in code context
"""

from __future__ import annotations

import re

NUMBER_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12", "twenty": "20",
    "hundred": "100",
}

SYMBOLS = [
    ("open parenthesis", "("), ("close parenthesis", ")"),
    ("open bracket", "["), ("close bracket", "]"),
    ("open brace", "{"), ("close brace", "}"),
    ("greater than or equal", ">="), ("less than or equal", "<="),
    ("not equals", "!="), ("double equals", "=="),
    ("greater than", ">"), ("less than", "<"),
    ("equals", "="), ("arrow", "->"), ("fat arrow", "=>"),
    ("plus", "+"), ("minus", "-"), ("star", "*"), ("slash", "/"),
    ("underscore", "_"), ("dot", "."), ("colon", ":"),
    ("semicolon", ";"), ("comma", ","), ("pipe", "|"),
    ("ampersand", "&"), ("hash", "#"), ("at sign", "@"),
]


def _identifier(words: list[str], mode: str) -> str:
    words = [w.lower() for w in words]
    if mode == "snake":
        return "_".join(words)
    if mode == "camel":
        return words[0] + "".join(w.capitalize() for w in words[1:])
    if mode == "pascal":
        return "".join(w.capitalize() for w in words)
    if mode == "constant":
        return "_".join(words).upper()
    return " ".join(words)


def _apply_case_modes(text: str) -> str:
    pat = re.compile(
        r"\b(snake|camel|pascal|constant)\s+case\s+"
        r"((?:\w+?\s+?){0,4}?\w+?)(?=\s+(?:equals|arrow|plus|minus|colon|"
        r"semicolon|comma|dot|open|close|new line)\b|$)",
        flags=re.I,
    )

    def repl(m: re.Match) -> str:
        return _identifier(m.group(2).split(), m.group(1).lower())

    return pat.sub(repl, text)


def to_code(text: str) -> str:
    """Convert dictated code speech into code-shaped text."""
    if not text or not text.strip():
        return ""
    out = _apply_case_modes(text.strip())
    for phrase, symbol in SYMBOLS:
        out = re.sub(rf"\s*\b{re.escape(phrase)}\b\s*",
                     f" {symbol} " if symbol in ("=", "->", "=>", "+",
                     "-", "*", "/", ">", "<", ">=", "<=", "!=", "==",
                     "|", "&") else symbol, out, flags=re.I)
    for word, digit in NUMBER_WORDS.items():
        out = re.sub(rf"\b{word}\b", digit, out, flags=re.I)
    out = re.sub(r"\(\s+", "(", out)
    out = re.sub(r"\s+\)", ")", out)
    out = re.sub(r"\s+\.", ".", out)
    out = re.sub(r"\s*:\s*$", ":", out.strip())
    out = re.sub(r"[ \t]{2,}", " ", out)
    # Tidy "name = 5" spacing produced above.
    out = re.sub(r"\s*=\s*", " = ", out)
    out = re.sub(r"\s*->\s*", " -> ", out)
    return out.strip()
