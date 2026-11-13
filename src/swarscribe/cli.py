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
import os
import secrets
import sys
from dataclasses import asdict
from pathlib import Path

from .analytics import Analytics
from .codemode import to_code
from .commands import apply_command
from .config import Config
from .dictionary import PersonalDictionary
from .meeting import analyse_meeting
from .pipeline import Pipeline
from .snippets import SnippetLibrary
from .transcribe import BackendUnavailable, TranscriptionError


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


def _speech_options(parser):
    parser.add_argument("--engine", choices=("auto", "whisper", "parakeet"))
    parser.add_argument("--model")
    parser.add_argument("--language")
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"))
    parser.add_argument("--local-only", action="store_true", default=None)


def _configured(args) -> Config:
    config = Config.load()
    fields = ("engine", "model", "language", "device", "local_only", "microphone", "mode", "toggle")
    config._overrides = []
    for field in fields:
        value = getattr(args, field, None)
        if value is not None:
            setattr(config, field, value)
            config._overrides.append(field)
    return config


def main(argv: list[str] | None = None) -> int:
    try:
        return _main(argv)
    except (BackendUnavailable, TranscriptionError, RuntimeError, OSError, ValueError) as exc:
        print(f"SwarScribe: {exc}", file=sys.stderr)
        return 1


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="swarscribe",
                                     description="Offline-first AI dictation")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("clean", help="Clean raw dictation text")
    p.add_argument("text")
    p.add_argument("--style", default=None)
    p.add_argument("--app", default=None)
    p.add_argument("--code", action="store_true")
    p.add_argument("--hinglish", action="store_true",
                   help="Hinglish mode: cleanup tuned for Hindi + English")
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
    _speech_options(p)
    p.add_argument("--chunks", action="store_true",
                   help="Emit JSON Lines partial/final events from a mono PCM16 WAV")

    p = sub.add_parser("translate", help="Look up a phrase in the limited English/Hindi phrasebook")
    p.add_argument("text")
    p.add_argument("--from-lang", default="en")
    p.add_argument("--to-lang", default="hi")

    sub.add_parser("stats", help="Show dictation analytics summary")

    p = sub.add_parser("app", help="Run the desktop dictation app")
    _speech_options(p)
    p.add_argument("--microphone", type=int)
    p.add_argument("--mode", choices=("normal", "smart", "code", "command", "meeting"))
    p.add_argument("--toggle", action="store_true", default=None)
    p.add_argument("--hotkey", action="store_true",
                   help="Hold a global hotkey anywhere instead of Enter")

    d = sub.add_parser("dict", help="Manage your personal dictionary")
    dsub = d.add_subparsers(dest="dict_cmd", required=True)
    dsub.add_parser("list", help="Show dictionary entries")
    pa = dsub.add_parser("add", help="Teach a word: dict add heard Correct")
    pa.add_argument("heard")
    pa.add_argument("correct", nargs="+")
    pr = dsub.add_parser("remove", help="Forget a word")
    pr.add_argument("heard")

    p = sub.add_parser("tray", help="Run SwarScribe in the system tray")
    _speech_options(p)

    pk = sub.add_parser("packs", help="Shareable dictionary/snippet packs")
    pksub = pk.add_subparsers(dest="packs_cmd", required=True)
    pksub.add_parser("list", help="List packs bundled in the repo")
    pe = pksub.add_parser("export", help="Export your words as a pack")
    pe.add_argument("name")
    pe.add_argument("path")
    pi = pksub.add_parser("import", help="Import a pack file")
    pi.add_argument("path")

    p = sub.add_parser("meeting-record",
                       help="Turn a meeting WAV into timestamped notes")
    p.add_argument("wav")
    p.add_argument("--out", default="meeting-notes.md")
    _speech_options(p)
    p.add_argument("--record", action="store_true",
                   help="Capture microphone audio and save it to the WAV path before generating notes")
    p.add_argument("--microphone", type=int)

    p = sub.add_parser("history", help="Show or export dictation history")
    p.add_argument("--export", action="store_true",
                   help="Print the session as Markdown")
    p.add_argument("--undo", action="store_true",
                   help="Remove the most recent entry")
    p.add_argument("--search", default="")

    sub.add_parser("models", help="List speech models and downloads")
    sub.add_parser("devices", help="List PortAudio devices and indices")
    p = sub.add_parser("model-download", help="Download and initialize a speech model")
    _speech_options(p)
    sub.add_parser("pair-token", help="Generate a private Android pairing token")
    p = sub.add_parser("pair-serve", help="Serve speech on a trusted HTTPS address")
    p.add_argument("--bind", required=True, help="Local IPv4 address to listen on")
    p.add_argument("--hostname", required=True, help="DNS name or IPv4 address on the TLS certificate")
    p.add_argument("--cert", required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--port", type=int, default=8443)

    p = sub.add_parser("dashboard", help="Serve the local dashboard API")
    p.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.cmd == "clean":
        result = _pipeline(args).process(
            args.text, style=args.style, app=args.app,
            code_mode=args.code)
        text = result.text
        if args.hinglish:
            from .hinglish import clean_hinglish
            text = clean_hinglish(text)
        print(text)
    elif args.cmd == "command":
        print(apply_command(args.text, args.do))
    elif args.cmd == "code":
        print(to_code(args.text))
    elif args.cmd == "meeting":
        with open(args.file) as fh:
            notes = analyse_meeting(fh.read())
        print(notes.to_markdown())
    elif args.cmd == "transcribe":
        from .app import process_dictation
        from .transcribe import transcribe_wav_bytes
        config = _configured(args)
        backend = config.backend()
        if args.chunks:
            from .streaming import iter_file_events
            for event in iter_file_events(
                    args.file, lambda wav: transcribe_wav_bytes(wav, backend, config.language),
                    partial_every=1.5):
                print(json.dumps(asdict(event)), flush=True)
        else:
            transcript = backend.transcribe(args.file, config.language)
            if not transcript.text.strip():
                raise TranscriptionError("No speech was recognized.")
            print(json.dumps({"engine": transcript.engine, "language": transcript.language,
                              "raw": transcript.text, "segments": [asdict(s) for s in transcript.segments],
                              "clean": process_dictation(transcript.text, config)}, indent=2))
    elif args.cmd == "translate":
        from .translate import translate_text
        print(translate_text(args.text, args.from_lang, args.to_lang))
    elif args.cmd == "stats":
        from .app import build_pipeline
        print(json.dumps(build_pipeline()[2].summary(), indent=2))
    elif args.cmd == "app":
        if args.hotkey:
            from .desktop import run_desktop
            run_desktop(_configured(args))
        else:
            from .app import run_app
            run_app(config=_configured(args))
    elif args.cmd == "dict":
        config = Config.load()
        if args.dict_cmd == "list":
            if not config.dictionary:
                print("Dictionary is empty. Teach it: "
                      "swarscribe dict add devbysafe devbysaif")
            for heard, correct in sorted(config.dictionary.items()):
                print(f"{heard} -> {correct}")
        elif args.dict_cmd == "add":
            correct = " ".join(args.correct)
            config.dictionary[args.heard.lower()] = correct
            config.save()
            print(f"Learned: {args.heard.lower()} -> {correct}")
        elif args.dict_cmd == "remove":
            gone = config.dictionary.pop(args.heard.lower(), None)
            config.save()
            print("Removed." if gone else "Not in the dictionary.")
    elif args.cmd == "tray":
        from .tray import run_tray
        run_tray(_configured(args))
    elif args.cmd == "packs":
        from pathlib import Path as _Path

        from .packs import Pack, export_pack, import_pack
        if args.packs_cmd == "list":
            packs_dir = _Path(__file__).resolve().parent.parent.parent \
                / "packs"
            found = sorted(packs_dir.glob("*.json")) \
                if packs_dir.exists() else []
            if not found:
                print("No bundled packs found.")
            for item in found:
                pack = Pack.load(item)
                print(f"{pack.name}: {len(pack.dictionary)} words, "
                      f"{len(pack.snippets)} snippets ({item.name})")
        elif args.packs_cmd == "export":
            config = Config.load()
            path = export_pack(config, args.name).save(_Path(args.path))
            print(f"Pack saved: {path}")
        elif args.packs_cmd == "import":
            config = Config.load()
            pack = Pack.load(_Path(args.path))
            added = import_pack(pack, config)
            config.save()
            print(f"Imported '{pack.name}': {added} new entries.")
    elif args.cmd == "meeting-record":
        from .meeting_recorder import save_meeting_notes
        from .transcribe import transcribe_wav_bytes
        config = _configured(args)
        backend = config.backend()
        if args.record:
            from .meeting_recorder import capture_meeting
            capture_meeting(args.wav, config.microphone)
        path = save_meeting_notes(
            args.wav,
            lambda data: transcribe_wav_bytes(data, backend, config.language),
            args.out)
        print(f"Meeting notes written: {path}")
    elif args.cmd == "history":
        from .app import state_dir
        from .history import History
        path = state_dir() / "history.json"
        history = History.load(path) if path.exists() else History()
        history.prune(Config.load().history_days)
        if args.undo:
            gone = history.undo()
            history.save(path)
            print("Undone:", gone.text if gone else "nothing to undo")
        elif args.export:
            print(history.export_markdown())
        else:
            if not history.entries:
                print("No dictations yet. Run: swarscribe app")
            entries = [entry for entry in history.entries
                       if args.search.casefold() in entry.text.casefold()]
            for entry in entries[-10:]:
                print("-", entry.text)
    elif args.cmd == "models":
        from .models import status
        print(json.dumps(status(), indent=2))
    elif args.cmd == "devices":
        try:
            import sounddevice
        except ImportError as exc:
            raise RuntimeError("Install the desktop extra to list audio devices.") from exc
        print(sounddevice.query_devices())
    elif args.cmd == "model-download":
        config = _configured(args)
        config.local_only = False
        print(f"Ready: {config.backend().name}")
    elif args.cmd == "pair-token":
        print(secrets.token_urlsafe(32))
    elif args.cmd == "pair-serve":
        import ipaddress
        import re
        import ssl
        try:
            import uvicorn
            from .api import create_app
        except ImportError as exc:
            raise RuntimeError("Install 'swarscribe[api]' to start pairing.") from exc
        ip = ipaddress.IPv4Address(args.bind)
        if ip.is_unspecified or ip.is_multicast:
            raise ValueError("Specify the actual desktop interface address, such as 192.168.1.15.")
        hostname = args.hostname.lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{0,252}", hostname):
            raise ValueError("Specify the certificate hostname without a URL scheme or port.")
        token = os.getenv("SWARSCRIBE_PAIR_TOKEN", "")
        if not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", token):
            raise ValueError("Set SWARSCRIBE_PAIR_TOKEN to the output of swarscribe pair-token.")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(Path(args.cert), Path(args.key))
        paired = create_app(lan_token=token, lan_hostname=hostname)
        print(f"Android pairing: https://{hostname}:{args.port}")
        uvicorn.run(paired, host=str(ip), port=args.port, ssl_certfile=args.cert,
                    ssl_keyfile=args.key, access_log=False, proxy_headers=False, ws="none")
    elif args.cmd == "dashboard":
        try:
            import uvicorn
        except ImportError:
            print("Dashboard needs the api extra: "
                  "pip install 'swarscribe[api]'")
            return 1
        print(f"Dashboard: http://127.0.0.1:{args.port}/")
        uvicorn.run("swarscribe.api:app", host="127.0.0.1", port=args.port,
                    access_log=False, proxy_headers=False, ws="none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
