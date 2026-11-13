"""Command line interface.

Examples:
  swarscribe clean "um the meeting is on monday no wait tuesday"
  swarscribe command --do "make it formal" --text "i can't make it"
  swarscribe code "snake case user name equals five"
  swarscribe meeting transcript.txt
  swarscribe transcribe recording.wav
  swarscribe stats
"""

from __future__ import annotations

import argparse
import json
import sys

from .analytics import Analytics
from .codemode import to_code
from .commands import apply_command
from .config import Config
from .dictionary import PersonalDictionary
from .meeting import analyse_meeting
from .pipeline import Pipeline
from .snippets import SnippetLibrary
from .transcribe import choose_backend


def _pipeline(args) -> Pipeline:
    config = Config.load()
    dictionary = config.to_dictionary()
    snippets = config.to_snippets()
    if getattr(args, "with_defaults", False):
        for k, v in PersonalDictionary.default_for_saif().entries.items():
            dictionary.add(k, v)
        for k, v in SnippetLibrary.defaults().snippets.items():
            snippets.add(k, v)
    return Pipeline(dictionary=dictionary, snippets=snippets,
                    analytics=Analytics())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="swarscribe",
                                     description="Offline-first AI dictation")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("clean", help="Clean raw dictation text")
    p.add_argument("text")
    p.add_argument("--style", default=None)
    p.add_argument("--app", default=None)
    p.add_argument("--code", action="store_true")
    p.add_argument("--with-defaults", action="store_true")

    p = sub.add_parser("command", help="Apply a voice editing command")
    p.add_argument("--do", required=True)
    p.add_argument("--text", required=True)

    p = sub.add_parser("code", help="Convert dictated code speech to code")
    p.add_argument("text")

    p = sub.add_parser("meeting", help="Turn a transcript into notes")
    p.add_argument("file")

    p = sub.add_parser("transcribe", help="Transcribe an audio file")
    p.add_argument("file")
    p.add_argument("--engine", default="auto")
    p.add_argument("--language", default=None)

    p = sub.add_parser("translate", help="Translate text (phrasebook + optional LLM)")
    p.add_argument("text")
    p.add_argument("--from-lang", default="en")
    p.add_argument("--to-lang", default="hi")

    sub.add_parser("stats", help="Show dictation analytics summary")

    p = sub.add_parser("app", help="Run the desktop dictation app")
    p.add_argument("--engine", default="auto")
    p.add_argument("--model", default=None)

    sub.add_parser("models", help="List speech models and downloads")

    p = sub.add_parser("dashboard", help="Serve the local dashboard API")
    p.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.cmd == "clean":
        result = _pipeline(args).process(
            args.text, style=args.style, app=args.app,
            code_mode=args.code)
        print(result.text)
    elif args.cmd == "command":
        print(apply_command(args.text, args.do))
    elif args.cmd == "code":
        print(to_code(args.text))
    elif args.cmd == "meeting":
        with open(args.file) as fh:
            notes = analyse_meeting(fh.read())
        print(notes.to_markdown())
    elif args.cmd == "transcribe":
        backend = choose_backend(args.engine, args.language)
        transcript = backend.transcribe(args.file, args.language)
        result = _pipeline(args).process(transcript.text)
        print(json.dumps({"engine": transcript.engine,
                          "raw": transcript.text,
                          "clean": result.text}, indent=2))
    elif args.cmd == "translate":
        from .translate import translate_text
        print(translate_text(args.text, args.from_lang, args.to_lang))
    elif args.cmd == "stats":
        print(json.dumps(Analytics().summary(), indent=2))
    elif args.cmd == "app":
        from .app import run_app
        run_app(engine=args.engine, model=args.model)
    elif args.cmd == "models":
        from .models import status
        print(json.dumps(status(), indent=2))
    elif args.cmd == "dashboard":
        try:
            import uvicorn
        except ImportError:
            print("Dashboard needs the api extra: "
                  "pip install 'swarscribe[api]'")
            return 1
        print(f"Dashboard API: http://127.0.0.1:{args.port}/docs")
        print("Stats: /stats  Models: /models  Dictionary: /dictionary")
        uvicorn.run("swarscribe.api:app", port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
