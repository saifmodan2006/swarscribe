# Hindi and mixed Hindi–English dictation

Set the desktop language to **Hindi** to give Whisper a Hindi hint. Set **Hindi + English** to select Whisper with automatic language detection. This uses transcription mode, so SwarScribe does not translate your words. Mixed speech can still come back in Devanagari, Latin script, or both depending on the model and sample.

```powershell
swarscribe transcribe .\speech.wav --engine whisper --model base --language hinglish
swarscribe clean --hinglish "matlab kal subah meeting hai aur bahot kaam hai"
swarscribe dict add "Super Base" Supabase
```

The optional text-only Hinglish cleanup normalizes a small set of Romanized variants and sentence-initial fillers. The default cleanup preserves mixed scripts and uses your dictionary to correct named terms. Android desktop mode offers the same Whisper auto routing; on-device mode uses the installed English or Hindi service. Neither engine guarantees word-by-word language switching.
