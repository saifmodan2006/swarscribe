import array
import unittest

from swarscribe.streaming import StreamingTranscriber, stream_file


def tone(ms=300, amp=2000, rate=16000):
    samples = array.array("h", [amp] * (rate * ms // 1000))
    return samples.tobytes()


def silence(ms=800, rate=16000):
    return bytes(rate * ms // 1000 * 2)


class FakeBackend:
    def __init__(self):
        self.calls = 0

    def __call__(self, wav):
        self.calls += 1
        return f"segment {self.calls}"


class TestStreaming(unittest.TestCase):
    def test_finalizes_on_pause(self):
        backend = FakeBackend()
        streamer = StreamingTranscriber(backend)
        events = []
        events += streamer.feed(tone(500))
        events += streamer.feed(silence(800))
        events += streamer.feed(tone(500))
        events += streamer.flush()
        finals = [e for e in events if e.kind == "final"]
        self.assertEqual(len(finals), 2)
        self.assertEqual(finals[0].segment, 0)
        self.assertEqual(finals[1].segment, 1)

    def test_short_blip_is_dropped(self):
        backend = FakeBackend()
        streamer = StreamingTranscriber(backend)
        events = streamer.feed(tone(100)) + streamer.flush()
        self.assertEqual(events, [])

    def test_stream_file_missing(self):
        with self.assertRaises(Exception):
            stream_file("/nonexistent.wav", FakeBackend())


if __name__ == "__main__":
    unittest.main()
