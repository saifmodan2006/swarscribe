# SwarScribe bots: dictate into the apps people already use

Two bots, one idea: send a voice note, get clean formatted text back.
Both run the local SwarScribe pipeline, so speech is transcribed on the
machine running the bot, not by a third-party dictation service.

## Telegram (LIVE: [@swarscribe_bot](https://t.me/swarscribe_bot))

The official SwarScribe bot is live: open it, tap Start, send a voice
note, get clean text back. It runs on a local Whisper model, and audio
is deleted right after each reply. To run your own instance instead,
the setup is below.

## Telegram (self-host, 5 minute setup)

1. Message @BotFather, send /newbot, copy the token.
2. `pip install "swarscribe[whisper]"` and make sure `ffmpeg` is installed.
3. Run it:

```bash
SWARSCRIBE_TELEGRAM_TOKEN=your-token python bots/telegram_bot.py
```

Open your bot, tap /start, send a voice note. Hindi and English both
work. Audio files are deleted immediately after the reply; nothing is
stored or logged.

## WhatsApp (official Cloud API)

1. Create a Meta developer app, add WhatsApp, note the access token and
   your test number.
2. Host the SwarScribe API somewhere reachable, mount the router from
   `bots/whatsapp_bot.py` (`create_router(pipeline, transcribe_media,
   sender)`), and register `https://your-host/whatsapp` as the webhook
   with your verify token in `SWARSCRIBE_WA_VERIFY_TOKEN`.
3. Voice notes arrive as media ids; your `transcribe_media` downloads
   them with the Cloud API media endpoint and runs them through
   `swarscribe.transcribe.transcribe_wav_bytes`, and `sender` replies
   with the messages endpoint. Both are thin wrappers over two HTTPS
   calls, kept injectable so the parsing and cleaning stay testable.

The webhook parsing and reply building are unit tested in
`tests/test_bots.py`. Meta's approval rules for production WhatsApp
numbers apply as usual; a test number works out of the box.
