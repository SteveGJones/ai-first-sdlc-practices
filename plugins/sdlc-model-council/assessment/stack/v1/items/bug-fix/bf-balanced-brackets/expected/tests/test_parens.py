"""Hidden tests for the balanced-brackets bug-fix item. Not shown to the model."""

import unittest

from parens import is_balanced


class TestIsBalanced(unittest.TestCase):
    def test_empty_string(self):
        self.assertTrue(is_balanced(""))

    def test_simple_pairs(self):
        self.assertTrue(is_balanced("()"))
        self.assertTrue(is_balanced("[]"))
        self.assertTrue(is_balanced("{}"))

    def test_nested(self):
        self.assertTrue(is_balanced("([{}])"))
        self.assertTrue(is_balanced("({[]})"))

    def test_sequential(self):
        self.assertTrue(is_balanced("()[]{}"))

    def test_mismatched_types_same_depth(self):
        self.assertFalse(is_balanced("(]"))
        self.assertFalse(is_balanced("[)"))
        self.assertFalse(is_balanced("{)"))

    def test_mismatched_nested(self):
        self.assertFalse(is_balanced("([)]"))

    def test_unclosed(self):
        self.assertFalse(is_balanced("("))
        self.assertFalse(is_balanced("(()"))

    def test_unopened(self):
        self.assertFalse(is_balanced(")("))
        self.assertFalse(is_balanced(")"))

    def test_no_brackets(self):
        self.assertTrue(is_balanced("hello world"))

    def test_mixed_text_balanced(self):
        self.assertTrue(is_balanced("f(x) = [a, b] + {c: d}"))


if __name__ == "__main__":
    unittest.main()
