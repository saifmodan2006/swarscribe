# FlowScribe Architecture

## Design principles

1. **Local first.** Transcription, cleanup, dictionary, snippets and
   analytics run on the user's machine. The cloud is an opt-in, never
   a requirement.
2. **No single model bet.** Two open source engines cover speed and
   language coverage; the pipeline picks per session.
3. **Deterministic core, optional AI.** The rule cleanup pipeline
   always works, offline, in milliseconds. An LLM pass (local Ollama
   or a user-configured endpoint) is an enhancement, never a dependency.
4. **Plain files the user owns.** Config, dictionary, snippets and
   history are JSON on disk. No account, no lock-in.

## Pipeline

```
microphone / audio file / pasted text
        |
        v
[ Transcription ]  Parakeet v3 (speed, English + 25 European)
                   or Whisper large-v3-turbo via faster-whisper
                   (99 languages, Hindi and Hinglish included)
        |
        v
[ Cleanup ]        fillers, repetitions, self-corrections,
                   spoken punctuation, spoken lists
        |
        v
[ Dictionary ]     personal terms and mis-hearing fixes
        |
        v
[ Snippets ]       spoken triggers -> saved text blocks
        |
        v
[ Code mode ]      optional: identifiers, symbols, digits
        |
        v
[ Style ]          per-app tone: email, chat, formal, document
        |
        v
[ LLM pass ]       optional, local Ollama or user endpoint
        |
        v
[ Output ]         typed at cursor (desktop), clipboard, API, file
        |
        v
[ Analytics ]      words, WPM, estimated time saved (local only)
```

## Modules

| Module | Job |
| --- | --- |
| `transcribe.py` | Dual-engine backends, lazy loading, graceful fallback |
| `cleanup.py` | The smart cleanup rule pipeline |
| `dictionary.py` | Personal dictionary with suggestions |
| `snippets.py` | Spoken trigger expansion |
| `styles.py` | Per-app writing styles |
| `commands.py` | Command Mode voice editing |
| `codemode.py` | Developer dictation: identifiers and symbols |
| `meeting.py` | Meeting Mode: summary, decisions, action items |
| `analytics.py` | Local dictation statistics |
| `llm.py` | Optional Ollama / OpenAI-compatible enhancement |
| `pipeline.py` | Orchestrates every stage |
| `desktop.py` | Push-to-talk hotkey and paste at cursor |
| `api.py` | FastAPI service wrapper |
| `cli.py` | Command line interface |
| `config.py` | Local JSON configuration |

## Why two engines

Parakeet TDT 0.6B v3 beats Whisper large-v3 on English word error
rate and runs many times faster, which is what live dictation feels
like. Whisper covers 99 languages, which Parakeet does not, and it
is the practical choice for Hindi and mixed Hindi-English speech.
FlowScribe routes by language instead of forcing one trade-off.

## Privacy model

- Audio never leaves the device in local mode.
- Transcripts, history and analytics stay in local files.
- The optional LLM pass prefers a local Ollama server.
- There is no telemetry. The analytics module counts words for the
  user, on the user's disk, for the user's own report.
