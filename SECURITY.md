# Security and Privacy

SwarScribe's security model is mostly a privacy model: in local mode your audio, transcripts, dictionary, snippets, history and analytics never leave your machine, so there is very little to leak.

## Reporting a problem

Please open a GitHub issue for non-sensitive bugs. For anything that could expose a user's dictation data, contact the maintainer first through the portfolio contact form at https://www.devbysaif.in/ so a fix can land before details are public.

## Notes for users

- The optional LLM pass can be pointed at a local Ollama server (private) or a cloud endpoint (your key, your choice). SwarScribe defaults to no LLM at all.
- Cloud transcription is never configured for you. The dual engines run locally; a backend only sends data if you install and choose one that does.
- Your config lives at `~/.swarscribe/config.json`. It is a plain file: inspect it, back it up, delete it, it is yours.
