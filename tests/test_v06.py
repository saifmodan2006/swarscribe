import tempfile
import unittest
from pathlib import Path

from swarscribe.config import Config
from swarscribe.hinglish import clean_hinglish
from swarscribe.meeting_recorder import MeetingNote, TimedSegment
from swarscribe.packs import Pack, export_pack, import_pack


class TestHinglish(unittest.TestCase):
    def test_leading_filler_removed(self):
        self.assertEqual(
            clean_hinglish("Matlab kal meeting hai."),
            "Kal meeting hai.")

    def test_mid_sentence_words_kept(self):
        out = clean_hinglish("Yeh matlab alag hai aur bahut important hai.")
        self.assertIn("matlab", out)

    def test_variant_normalized(self):
        self.assertEqual(clean_hinglish("Bahot accha kaam."),
                         "Bahut accha kaam.")


class TestPacks(unittest.TestCase):
    def test_round_trip(self):
        config = Config()
        config.dictionary["safe"] = "Saif"
        config.snippets["sig"] = "Regards, Saif"
        pack = export_pack(config, "mine")
        with tempfile.TemporaryDirectory() as tmp:
            path = pack.save(Path(tmp) / "pack.json")
            loaded = Pack.load(path)
        other = Config()
        added = import_pack(loaded, other)
        self.assertEqual(added, 2)
        self.assertEqual(other.dictionary["safe"], "Saif")


class TestMeetingNoteMarkdown(unittest.TestCase):
    def test_markdown_shape(self):
        note = MeetingNote(
            title="Weekly sync",
            segments=[TimedSegment(0.0, "We decided to ship Friday."),
                      TimedSegment(65.0, "Saif will write the notes.")],
            summary="Ship on Friday.",
            decisions=["Ship Friday."],
            actions=["Write the notes."])
        md = note.to_markdown()
        self.assertIn("# Weekly sync", md)
        self.assertIn("**[01:05]**", md)
        self.assertIn("- [ ] Write the notes.", md)
        self.assertEqual(note.transcript,
                         "We decided to ship Friday. "
                         "Saif will write the notes.")


if __name__ == "__main__":
    unittest.main()
