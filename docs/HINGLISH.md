# Hinglish Mode

India does not dictate in one language. It says "kal subah meeting
hai, please send the file before that" in one breath, and generic
dictation tools mangle the Hindi half or "correct" it into English.

SwarScribe's Hinglish mode is built for the mix:

- **Transcription** routes to Whisper with the Hindi language hint, so
  mixed speech is heard as mixed speech, not forced into one language.
- **Cleanup keeps the mix.** Hindi words are never translated or
  anglicized. Only clear sentence-initial discourse fillers (a leading
  "matlab", "arre") are removed, and only where they carry no meaning;
  the same words mid-sentence are left untouched.
- **Spelling is normalized** for the variants Whisper hears
  inconsistently (bahot and bohot both land as bahut), with
  capitalization preserved.
- **Word packs** ship for everyday Hinglish (`packs/hinglish-everyday.json`),
  and your own names and places are one `swarscribe dict add` away.

Try it:

```bash
swarscribe clean --hinglish "matlab kal subah meeting hai aur bahot kaam hai"
# Kal subah meeting hai aur bahut kaam hai.
```

Hinglish mode is young and honest about it: it handles the common
patterns today, and the phrasebook approach means every correction
users teach it makes the next dictation better.
