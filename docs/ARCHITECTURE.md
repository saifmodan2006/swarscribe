# SwarScribe architecture

The Windows tray, Python CLI and local API share the speech backend and rule pipeline. Android and the web demo have smaller client-side cleanup implementations.

| Surface | Audio path | Output |
|---|---|---|
| Windows hotkey / tray | PortAudio capture, one recording at a time, then cached speech model | Guarded Windows Unicode input or previewed selection command; optional history |
| Terminal and API | File, microphone, or bounded WAV payload → cached speech model | Terminal, JSON, optional local history |
| Meeting CLI | Mono PCM16 WAV on disk → bounded chunks and speech model | Local Markdown with model or chunk timestamps |
| Android keyboard and on-device companion | Android on-device speech service | InputConnection or companion preview |
| Android paired companion | Bounded PCM16 WAV → explicit HTTPS pairing endpoint → desktop model | Companion preview |
| Web demo | Typed/pasted text or optional browser speech service | Page preview and explicit copy |

`transcribe.py` defines the audio backend contract, bounded process-local cache and timestamps. Explicit engine requests fail rather than switching engines; auto may fall back at initialization. `streaming.py` emits partial previews and stable finals with source offsets for file replay. It does not use a native incremental model.

`pipeline.py` applies smart cleanup, personal dictionary, snippets, Code Mode or style. `app.py` and `config.py` share preferences and data between entry points. Local JSON files are replaced atomically; writes within an API process are serialized. Separate processes writing at the same time can still lose updates. `windows.py` checks the foreground editor and avoids clipboard mutation. Selected-text commands recheck the selection after preview.

`api.py` serves packaged dashboard assets and JSON from the same loopback origin. Its separate paired mode exposes only the authenticated speech and health routes. Read [security and privacy](../SECURITY.md) for the network boundaries and data retention.
