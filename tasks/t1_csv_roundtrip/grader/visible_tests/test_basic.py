"""Existing tinycsv tests. Run with:  python -m unittest discover -s tests"""
import unittest

import tinycsv


class BasicTests(unittest.TestCase):
    def test_simple_read(self):
        self.assertEqual(tinycsv.read("a,b,c\n1,2,3\n"), [["a", "b", "c"], ["1", "2", "3"]])

    def test_quoted_delimiter_read(self):
        self.assertEqual(tinycsv.read('name,city\nAsha,"Pune, MH"\n'),
                         [["name", "city"], ["Asha", "Pune, MH"]])

    def test_simple_write(self):
        self.assertEqual(tinycsv.write([["a", "b"], ["1", "2"]]), "a,b\n1,2\n")

    def test_write_quotes_delimiter(self):
        self.assertEqual(tinycsv.write([["Pune, MH"]]), '"Pune, MH"\n')

    def test_custom_delimiter(self):
        self.assertEqual(tinycsv.read("a;b\n"), [["a;b"]])
        self.assertEqual(tinycsv.read("a;b\n", delimiter=";"), [["a", "b"]])

    def test_empty_fields(self):
        self.assertEqual(tinycsv.read("a,,c\n"), [["a", "", "c"]])


if __name__ == "__main__":
    unittest.main()
