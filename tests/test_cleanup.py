import unittest

from flowscribe.cleanup import clean_text


class TestCleanup(unittest.TestCase):
    def test_removes_fillers(self):
        self.assertEqual(clean_text("um I uh want to send this"),
                         "I want to send this.")

    def test_spoken_punctuation(self):
        self.assertEqual(
            clean_text("hello comma how are you question mark"),
            "Hello, how are you?")

    def test_self_correction_single_word(self):
        self.assertEqual(
            clean_text("the meeting is on monday no wait tuesday at five"),
            "The meeting is on Tuesday at five.")

    def test_self_correction_anchored_phrase(self):
        self.assertEqual(
            clean_text("the call is at five, no wait, at six pm"),
            "The call is at six pm.")

    def test_repetition_removed(self):
        self.assertEqual(clean_text("this is is the the plan"),
                         "This is the plan.")

    def test_spoken_list(self):
        self.assertEqual(
            clean_text("first apples second bananas third oranges"),
            "- apples\n- bananas\n- oranges")

    def test_empty(self):
        self.assertEqual(clean_text(""), "")
        self.assertEqual(clean_text("   "), "")

    def test_new_paragraph(self):
        out = clean_text("first line new paragraph second line")
        self.assertIn("\n\n", out)
        self.assertTrue(out.startswith("First line"))


if __name__ == "__main__":
    unittest.main()
