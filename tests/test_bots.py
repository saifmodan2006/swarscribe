import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bots"))

from swarscribe.pipeline import Pipeline
from swarscribe.transcribe import EchoBackend
from telegram_bot import VoiceNoteBot
from whatsapp_bot import build_reply, parse_message_event, verify_challenge


class FakeAPI:
    def __init__(self):
        self.sent = []

    def call(self, method, **params):
        self.sent.append((method, params))
        return {}

    def download(self, file_id):
        return b"fake-ogg"


class TestTelegramBot(unittest.TestCase):
    def setUp(self):
        self.api = FakeAPI()
        self.bot = VoiceNoteBot(
            self.api, Pipeline(), EchoBackend("um hello there"),
            converter=lambda data: data)

    def test_start_message(self):
        reply = self.bot.handle_update(
            {"message": {"chat": {"id": 7}, "text": "/start"}})
        self.assertIn("voice note", reply)
        self.assertEqual(self.api.sent[0][0], "sendMessage")

    def test_text_message_is_cleaned(self):
        reply = self.bot.handle_update(
            {"message": {"chat": {"id": 7},
                         "text": "um the meeting is on monday"}})
        self.assertEqual(reply, "The meeting is on Monday.")

    def test_voice_message_replies(self):
        # EchoBackend ignores audio content, so the wav bytes are a stub
        import telegram_bot
        original = telegram_bot.transcribe_file
        telegram_bot.transcribe_file = (
            lambda path, backend=None: EchoBackend("um hello there")
            .transcribe(path))
        try:
            reply = self.bot.handle_update(
                {"message": {"chat": {"id": 7},
                             "voice": {"file_id": "f1"}}})
        finally:
            telegram_bot.transcribe_file = original
        self.assertEqual(reply, "Hello there.")

    def test_non_message_update_skipped(self):
        self.assertIsNone(self.bot.handle_update({"edited_message": {}}))


class TestWhatsAppParsing(unittest.TestCase):
    PAYLOAD = {"entry": [{"changes": [{"value": {"messages": [
        {"from": "919999999999", "type": "audio",
         "audio": {"id": "media-1"}}]}}]}]}

    def test_parse_audio_event(self):
        event = parse_message_event(self.PAYLOAD)
        self.assertEqual(event["kind"], "audio")
        self.assertEqual(event["media_id"], "media-1")

    def test_parse_garbage(self):
        self.assertIsNone(parse_message_event({}))
        self.assertIsNone(parse_message_event({"entry": []}))

    def test_verify_challenge(self):
        params = {"hub.mode": "subscribe", "hub.verify_token": "tok",
                  "hub.challenge": "42"}
        self.assertEqual(verify_challenge(params, "tok"), "42")
        self.assertIsNone(verify_challenge(params, "wrong"))

    def test_build_reply_text(self):
        event = {"kind": "text", "text": "um hello there", "from": "1"}
        reply = build_reply(event, Pipeline(), lambda mid: "")
        self.assertEqual(reply, "Hello there.")


if __name__ == "__main__":
    unittest.main()
