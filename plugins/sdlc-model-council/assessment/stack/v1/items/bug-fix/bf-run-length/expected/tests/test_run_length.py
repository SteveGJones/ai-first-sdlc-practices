"""Hidden tests for the run-length-encoding bug-fix item. Not shown to the model."""

import unittest

from run_length import decode, encode


class TestRunLength(unittest.TestCase):
    def test_encode_basic(self):
        self.assertEqual(encode("aaabbc"), [("a", 3), ("b", 2), ("c", 1)])

    def test_encode_empty(self):
        self.assertEqual(encode(""), [])

    def test_encode_single_char(self):
        self.assertEqual(encode("zzzz"), [("z", 4)])

    def test_decode_basic(self):
        self.assertEqual(decode([("a", 3), ("b", 2), ("c", 1)]), "aaabbc")

    def test_decode_empty(self):
        self.assertEqual(decode([]), "")

    def test_decode_single_run(self):
        self.assertEqual(decode([("x", 1)]), "x")

    def test_round_trip(self):
        for s in ["aaabbbccccd", "hello", "mississippi", "a", ""]:
            self.assertEqual(decode(encode(s)), s)


if __name__ == "__main__":
    unittest.main()
