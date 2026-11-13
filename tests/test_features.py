import unittest

from flowscribe.analytics import Analytics
from flowscribe.codemode import to_code
from flowscribe.commands import apply_command
from flowscribe.dictionary import PersonalDictionary
from flowscribe.meeting import analyse_meeting
from flowscribe.pipeline import Pipeline
from flowscribe.snippets import SnippetLibrary
from flowscribe.styles import apply_style


class TestDictionaryAndSnippets(unittest.TestCase):
    def test_dictionary_replaces_mishearing(self):
        d = PersonalDictionary.default_for_saif()
        self.assertIn("devbysaif", d.apply("check devbysafe today"))

    def test_snippet_expands(self):
        lib = SnippetLibrary.defaults()
        out = lib.expand("See my portfolio for details.")
        self.assertIn("https://www.devbysaif.in/", out)


class TestStylesAndCommands(unittest.TestCase):
    def test_formal_expands_contractions(self):
        self.assertEqual(apply_style("I can't do it.", "formal"),
                         "I cannot do it.")

    def test_email_style_greeting(self):
        self.assertEqual(apply_style("hi team, we can't ship", "email"),
                         "Hello team, we cannot ship")

    def test_command_formal(self):
        self.assertEqual(apply_command("i can't make it", "make it formal"),
                         "I cannot make it")

    def test_command_shorten(self):
        self.assertEqual(
            apply_command("This is really very important and just urgent.",
                          "make it shorter"),
            "This is important and urgent.")

    def test_command_bullet_list(self):
        self.assertEqual(
            apply_command("apples, bananas and oranges", "make it a list"),
            "- apples\n- bananas\n- oranges")

    def test_unknown_command_is_safe(self):
        self.assertEqual(apply_command("keep me", "dance for me"), "keep me")


class TestCodeMode(unittest.TestCase):
    def test_snake_case_assignment(self):
        self.assertEqual(to_code("snake case user name equals five"),
                         "user_name = 5")

    def test_camel_case(self):
        self.assertEqual(to_code("camel case user name"), "userName")

    def test_function_shape(self):
        self.assertEqual(
            to_code("function open parenthesis close parenthesis colon"),
            "function():")


class TestMeeting(unittest.TestCase):
    TRANSCRIPT = (
        "We discussed the launch plan for the new dictation feature in "
        "detail today. We decided to ship the offline version first. "
        "Rahul will prepare the demo by Friday. We agreed the pricing "
        "stays free for students. Priya needs to review the "
        "documentation before release.")

    def test_extracts_decisions_and_actions(self):
        notes = analyse_meeting(self.TRANSCRIPT)
        self.assertEqual(len(notes.decisions), 2)
        self.assertEqual(len(notes.action_items), 2)
        self.assertTrue(notes.summary)

    def test_markdown_shape(self):
        md = analyse_meeting(self.TRANSCRIPT).to_markdown()
        self.assertIn("## Action Items", md)
        self.assertIn("- [ ]", md)


class TestAnalytics(unittest.TestCase):
    def test_time_saved(self):
        a = Analytics()
        a.record(" ".join(["word"] * 60), seconds=60)
        summary = a.summary()
        self.assertEqual(summary["total_words"], 60)
        self.assertEqual(summary["average_wpm"], 60.0)
        self.assertEqual(summary["minutes_saved"], 0.5)


class TestPipeline(unittest.TestCase):
    def test_full_pipeline(self):
        pipe = Pipeline(dictionary=PersonalDictionary.default_for_saif(),
                        snippets=SnippetLibrary.defaults())
        result = pipe.process("um check devbysafe and my portfolio")
        self.assertIn("devbysaif", result.text)
        self.assertIn("https://www.devbysaif.in/", result.text)
        self.assertIn("cleanup", result.stages)

    def test_style_in_pipeline(self):
        result = Pipeline().process("i can't do it", style="formal")
        self.assertEqual(result.text, "I cannot do it.")


if __name__ == "__main__":
    unittest.main()
