import unittest

from swarscribe.cleanup import clean_text
from swarscribe.commands import apply_command
from swarscribe.dictionary import PersonalDictionary
from swarscribe.formats import parse_number_words
from swarscribe.history import History
from swarscribe.learn import learn_from_edit
from swarscribe.pipeline import Pipeline
from swarscribe.translate import translate_text


class TestSmartFormats(unittest.TestCase):
    def test_email_from_speech(self):
        self.assertEqual(
            clean_text("my email is saif modan at gmail dot com"),
            "My email is saifmodan@gmail.com.")

    def test_website_from_speech(self):
        self.assertEqual(clean_text("check devbysaif dot in today"),
                         "Check devbysaif.in today.")

    def test_time_with_minutes(self):
        self.assertEqual(
            clean_text("the call is at five thirty pm"),
            "The call is at 5:30 PM.")

    def test_time_hour_only(self):
        self.assertEqual(clean_text("we start at five pm"),
                         "We start at 5 PM.")

    def test_date(self):
        self.assertEqual(
            clean_text("the launch is on fifteen november 2026"),
            "The launch is on 15 November 2026.")

    def test_amount(self):
        self.assertEqual(
            clean_text("please send five hundred rupees to rahul"),
            "Please send 500 rupees to rahul.")

    def test_prose_numbers_untouched(self):
        self.assertEqual(clean_text("one of us will go"),
                         "One of us will go.")

    def test_number_parser(self):
        self.assertEqual(parse_number_words(["two", "thousand"]), 2000)
        self.assertEqual(parse_number_words(["five", "hundred", "fifty"]),
                         550)
        self.assertIsNone(parse_number_words(["banana"]))


class TestAutoLearn(unittest.TestCase):
    def test_learns_single_word_swap(self):
        pairs = learn_from_edit("Check devbysafe today.",
                                "Check devbysaif today.")
        self.assertEqual(pairs, [("devbysafe", "devbysaif")])

    def test_ignores_rewrites(self):
        pairs = learn_from_edit("Hello world.",
                                "A completely different sentence here.")
        self.assertEqual(pairs, [])

    def test_pipeline_learn(self):
        history = History()
        pipe = Pipeline(history=history)
        pipe.process("check devbysafe today")
        learned = pipe.learn("Check devbysaif today.")
        self.assertEqual(learned, [("devbysafe", "devbysaif")])
        again = pipe.process("check devbysafe today")
        self.assertIn("devbysaif", again.text)


class TestCommandChains(unittest.TestCase):
    def test_chain_formal_and_shorten(self):
        out = apply_command("i can't really do it",
                            "make it formal and shorten it")
        self.assertEqual(out, "I cannot do it")

    def test_single_command_still_works(self):
        self.assertEqual(apply_command("abc", "uppercase"), "ABC")


class TestTranslate(unittest.TestCase):
    def test_phrasebook_en_to_hi(self):
        self.assertEqual(translate_text("thank you", "en", "hi"),
                         "धन्यवाद")

    def test_phrasebook_hi_to_en(self):
        self.assertEqual(translate_text("धन्यवाद", "hi", "en"),
                         "thank you")

    def test_unknown_returns_original(self):
        self.assertEqual(translate_text("some unknown sentence", "en", "hi"),
                         "some unknown sentence")


class TestHistoryAndStats(unittest.TestCase):
    def test_undo(self):
        h = History()
        h.add("raw one", "Clean one.")
        h.add("raw two", "Clean two.")
        gone = h.undo()
        self.assertEqual(gone.text, "Clean two.")
        self.assertEqual(h.last().text, "Clean one.")

    def test_export_markdown(self):
        h = History()
        h.add("raw", "Clean text.")
        self.assertIn("Clean text.", h.export_markdown())

    def test_pipeline_stats(self):
        result = Pipeline().process("um hello there")
        self.assertEqual(result.stats["raw_words"], 3)
        self.assertEqual(result.stats["clean_words"], 2)
        self.assertGreaterEqual(result.stats["edits_made"], 1)


if __name__ == "__main__":
    unittest.main()
