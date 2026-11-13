import tempfile
import unittest
from pathlib import Path

from swarscribe.config import Config
from swarscribe.history import History


class TestDictRoundTrip(unittest.TestCase):
    def test_add_save_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            config = Config()
            config.dictionary["devbysafe"] = "devbysaif"
            config.save(path)
            loaded = Config.load(path)
            self.assertEqual(loaded.dictionary["devbysafe"], "devbysaif")
            pipe_dict = loaded.to_dictionary()
            out = pipe_dict.apply("check devbysafe today")
            self.assertIn("devbysaif", out)


class TestHistoryFile(unittest.TestCase):
    def test_save_load_undo(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.json"
            history = History()
            history.add("raw one", "Clean one.")
            history.add("raw two", "Clean two.")
            history.save(path)
            loaded = History.load(path)
            self.assertEqual(len(loaded.entries), 2)
            gone = loaded.undo()
            self.assertEqual(gone.text, "Clean two.")
            self.assertIn("Clean one.", loaded.export_markdown())


if __name__ == "__main__":
    unittest.main()
