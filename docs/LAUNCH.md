# Launch kit

Ready-to-use copy for telling the world about SwarScribe. Written in
Saif's voice: concrete, build-first, no hype words, no em dashes.

## LinkedIn post (primary, as published 2026-11-13)

I built a free, open source alternative to Wispr Flow. It is called SwarScribe.

Wispr Flow is good, but every word you dictate goes to the cloud, the free plan caps at 2,000 words a week, and key features sit behind a subscription.

SwarScribe runs fully on your own device. Free, open source, no word caps, no account.

What it can do:

Transcription
- Dual engine: NVIDIA Parakeet v3 for fast English, Whisper for 99 languages
- Streaming dictation: words land while you speak
- Hinglish mode, built for mixed Hindi and English speech

Smart cleanup
- Fillers and stutters removed, self-corrections resolved automatically
- Spoken punctuation, emails, websites, times, dates and amounts land written
- Personal dictionary that learns your names and words, plus shareable word packs
- Snippets and per-app styles: formal in email, casual in chat

Modes professionals use daily
- Command Mode: select text and say "make it formal" or "make it shorter"
- Code Mode: dictate real code, "snake case user name equals five" becomes user_name = 5
- Meeting Mode: a recording becomes a summary, decisions and action items

Everywhere you work
- Desktop app with hotkey and system tray (Windows, Mac, Linux)
- Android app, system keyboard, and a floating mic bubble
- Telegram bot: send a voice note to @swarscribe_bot, get clean text back
- Chrome extension, VS Code and Obsidian integrations
- Live web demo: no install, nothing uploaded

Measured, not marketed: on a small CPU, both local engines scored zero word errors on the benchmark clip at 5 to 8x real time. The benchmark script ships in the repo, run it yourself.

Say it. It is written.

Repo, live demo and the Telegram bot are in the comments. If you try it, tell me what breaks. That feedback makes v0.7.

First comment: Repo: https://github.com/saifmodan2006/swarscribe
Live demo, no install: https://saifmodan2006.github.io/swarscribe/web/

## Show HN

Show HN: SwarScribe, offline-first AI dictation (Parakeet + Whisper, MIT)

Body: Local-first dictation for desktop and Android. Dual-engine
transcription, deterministic cleanup pipeline (about 63k words per
second), Command and Code modes, meeting notes, Hinglish support.
Benchmarks and methodology in docs/BENCHMARKS.md. Built in the open,
one day, six releases. Feedback on the cleanup rules especially
welcome, they are plain Python and easy to extend.

## Reddit r/opensource

Title: I built an offline-first alternative to Wispr Flow and open sourced it (MIT)

Body points: why (privacy, caps, price), what it does, honest limits
(Android app compiled in CI, first physical-phone run pending; iOS on
the roadmap), links to repo, demo and benchmarks.

## Product Hunt (when ready)

Tagline: Say it. It is written. Offline-first AI dictation, free forever.
Maker comment draft mirrors the LinkedIn post, shorter, ending with:
the one feature I use daily is Code Mode, dictating snake_case without
fighting the recognizer.

## Launch checklist

- [x] LinkedIn post published 2026-11-13: https://www.linkedin.com/feed/update/urn:li:activity:7527005055250563072/ (first attempt failed on LinkedIn's PNG image upload; JPG worked)
- [ ] Show HN submission
- [ ] r/opensource and r/selfhosted posts
- [x] Telegram bot live with a BotFather token, link added to README (https://t.me/swarscribe_bot, verified end to end 2026-11-13)
- [ ] First physical-phone run of the Android APK, notes into android/README.md
- [ ] Product Hunt scheduled after the phone run
