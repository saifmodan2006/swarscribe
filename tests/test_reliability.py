import base64
import io
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

from swarscribe.app import build_pipeline, persist_result, process_dictation
from swarscribe.config import Config
from swarscribe.desktop import HotkeyState
from swarscribe.streaming import StreamingTranscriber
from swarscribe.transcribe import BackendUnavailable, Segment, Transcript, choose_backend


class BackendTests(unittest.TestCase):
    @patch("swarscribe.transcribe._load")
    def test_auto_reports_unavailable_engines(self, load):
        load.side_effect = [BackendUnavailable("NeMo unavailable"),
                            BackendUnavailable("Whisper unavailable")]
        with self.assertRaisesRegex(BackendUnavailable, "NeMo unavailable Whisper unavailable"):
            choose_backend(language="en")
        self.assertEqual([call.args[0] for call in load.call_args_list], ["parakeet", "whisper"])

    @patch("swarscribe.transcribe._load")
    def test_explicit_parakeet_fails_for_hinglish_before_loading(self, load):
        with self.assertRaisesRegex(BackendUnavailable, "does not support"):
            choose_backend("parakeet", "hinglish")
        load.assert_not_called()

    @patch("swarscribe.transcribe._load")
    def test_multilingual_auto_selects_whisper(self, load):
        choose_backend("auto", "hinglish")
        self.assertEqual(load.call_args.args[0], "whisper")


class DesktopTests(unittest.TestCase):
    def test_push_to_talk_requires_chord_and_member_release(self):
        keys = HotkeyState("ctrl+win")
        self.assertIsNone(keys.update("ctrl", True))
        self.assertEqual(keys.update("win", True), "start")
        self.assertIsNone(keys.update("win", True))
        self.assertIsNone(keys.update("x", False))
        self.assertEqual(keys.update("win", False), "stop")
        self.assertIsNone(keys.update("ctrl", False))

    def test_toggle_ignores_release_and_key_repeat(self):
        keys = HotkeyState("f9", toggle=True)
        self.assertEqual(keys.update("f9", True), "start")
        self.assertIsNone(keys.update("f9", True))
        self.assertIsNone(keys.update("f9", False))
        self.assertEqual(keys.update("f9", True), "stop")


class ProcessingTests(unittest.TestCase):
    def test_code_mode_python_javascript_sql(self):
        config = Config(mode="code", style="formal")
        examples = [
            ("function definition add open parenthesis x close parenthesis colon new line indent return x plus two",
             "def add(x):\n    return x + 2"),
            ("let x equals one new line x double equals two", "let x = 1\nx == 2"),
            ("SELECT id comma name FROM users new line WHERE id equals two",
             "SELECT id, name FROM users\nWHERE id = 2"),
        ]
        for raw, expected in examples:
            with self.subTest(raw=raw):
                self.assertEqual(process_dictation(raw, config), expected)
        self.assertEqual(process_dictation("a double equals sign", Config(mode="normal")),
                         "a double equals sign")

    def test_hinglish_preserves_technical_words_and_user_corrections(self):
        config = Config(dictionary={"super base": "Supabase"})
        self.assertEqual(process_dictation("कल Super Base deploy करना है", config),
                         "कल Supabase deploy करना है")

    def test_history_persistence_and_opt_out(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict("os.environ", SWARSCRIBE_HOME=folder):
            config = Config()
            persist_result("Super Base", "Supabase", 4, config)
            config.keep_history = False
            persist_result("private", "Private", 4, config)
            _, history, analytics = build_pipeline()
            self.assertEqual([entry.text for entry in history.entries], ["Supabase"])
            self.assertEqual(analytics.summary()["sessions"], 2)
            self.assertTrue((Path(folder) / "history.json").exists())

    def test_stream_silence_offsets_and_cancellation(self):
        output = Transcript("hello", "test", segments=(Segment(.1, .4, "hello"),))
        streamer = StreamingTranscriber(lambda _: output, sample_rate=1000, max_segment_ms=1000)
        self.assertEqual(streamer.feed(bytes(4000)), [])
        streamer.feed(b"\xd0\x07" * 500)
        self.assertEqual(streamer.poll_partial().kind, "partial")
        streamer.cancel()
        self.assertEqual(streamer.flush(), [])
        events = streamer.feed(b"\xd0\x07" * 1000)
        self.assertEqual(events[0].timing, "model")
        self.assertAlmostEqual(events[0].start_seconds, 2.6)


def wav(frames=1600, rate=16000):
    handle = io.BytesIO()
    with wave.open(handle, "wb") as out:
        out.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        out.writeframes(b"\x01\x01" * frames)
    return base64.b64encode(handle.getvalue()).decode("ascii")
