"""Existing pathmatch tests. Run with:  python -m unittest discover -s tests"""
import unittest

from pathmatch import filter_paths, match


class MatchTests(unittest.TestCase):
    def test_star_stays_in_segment(self):
        self.assertTrue(match("src/*.py", "src/app.py"))
        self.assertFalse(match("src/*.py", "src/pkg/app.py"))

    def test_question_mark(self):
        self.assertTrue(match("v?.txt", "v1.txt"))
        self.assertFalse(match("v?.txt", "v10.txt"))
        self.assertFalse(match("a?b", "a/b"))

    def test_classes(self):
        self.assertTrue(match("log[0-9].txt", "log7.txt"))
        self.assertFalse(match("log[!0-9].txt", "log7.txt"))
        self.assertFalse(match("a[!x]b", "a/b"))

    def test_literal_chars(self):
        self.assertTrue(match("a+b(1).txt", "a+b(1).txt"))
        self.assertTrue(match("x[y", "x[y"))

    def test_full_match(self):
        self.assertFalse(match("src", "src/app.py"))

    def test_doublestar_one_level(self):
        self.assertTrue(match("src/**/test_*.py", "src/unit/test_a.py"))

    def test_filter_keeps_order(self):
        self.assertEqual(filter_paths("*.md", ["b.md", "a.py", "a.md"]), ["b.md", "a.md"])


if __name__ == "__main__":
    unittest.main()
