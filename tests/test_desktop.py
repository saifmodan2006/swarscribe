import array
import io
import unittest
import wave

from swarscribe import models
from swarscribe.recorder import AudioBuffer
from swarscribe.vad import is_silence, speech_bounds, trim_silence


def tone(n, amp=2000):
    return array.array("h", [amp] * n)


def silence(n):
    return array.array("h", [0] * n)


class TestVad(unittest.TestCase):
    def test_pure_silence(self):
        self.assertTrue(is_silence(silence(16000)))
        self.assertEqual(speech_bounds(silence(16000)), (0, 0))

    def test_trim_keeps_speech(self):
        samples = silence(4800) + tone(9600) + silence(4800)
        trimmed = trim_silence(samples)
        self.assertGreater(len(trimmed), 8000)
        self.assertLess(len(trimmed), len(samples))
        self.assertTrue(any(s != 0 for s in trimmed))

    def test_bounds_cover_the_tone(self):
        samples = silence(16000) + tone(16000)
        start, end = speech_bounds(samples)
        self.assertLessEqual(start, 16000)
        self.assertGreater(end, 16000)


class TestAudioBuffer(unittest.TestCase):
    def test_wav_round_trip(self):
        buf = AudioBuffer()
        buf.add(silence(2400).tobytes())
        buf.add(tone(9600).tobytes())
        data = buf.wav_bytes()
        with wave.open(io.BytesIO(data)) as w:
            self.assertEqual(w.getnchannels(), 1)
            self.assertEqual(w.getframerate(), 16000)
            self.assertGreater(w.getnframes(), 8000)

    def test_seconds(self):
        buf = AudioBuffer()
        buf.add(tone(16000).tobytes())
        self.assertAlmostEqual(buf.seconds, 1.0, places=2)

    def test_empty_buffer_is_silent(self):
        self.assertTrue(AudioBuffer().silent())


class TestModels(unittest.TestCase):
    def test_registry(self):
        names = [m["name"] for m in models.status()]
        self.assertIn("parakeet-tdt-0.6b-v3", names)
        self.assertIn("large-v3-turbo", names)

    def test_recommendations(self):
        self.assertEqual(models.recommended().engine, "parakeet")
        self.assertEqual(models.recommended(hindi=True).engine, "whisper")

    def test_unknown_model(self):
        with self.assertRaises(KeyError):
            models.get("not-a-model")


if __name__ == "__main__":
    unittest.main()
