from django.test import SimpleTestCase

from ..search_utils import normalize, swap_layout, words
from ..templatetags.search_tags import highlight


class NormalizeTests(SimpleTestCase):
    def test_normalize(self):
        self.assertEqual(normalize("  Python   Ёлка!! "), "python елка")
        self.assertEqual(normalize("C++ и C#"), "c++ и c#")
        self.assertEqual(len(normalize("а" * 500)), 100)

    def test_words(self):
        self.assertEqual(words("UX/UI дизайнер"), ["ux", "ui", "дизайнер"])

    def test_layout(self):
        self.assertEqual(swap_layout("ghjuh"), "прогр")
        self.assertEqual(swap_layout("зш"), "pi")


class HighlightTests(SimpleTestCase):
    def test_marks(self):
        self.assertEqual(str(highlight("Python-разработчик", "pyt")), "<mark>Pyt</mark>hon-разработчик")

    def test_escape(self):
        self.assertEqual(str(highlight("<b>SQL</b>", "sql")), "&lt;b&gt;<mark>SQL</mark>&lt;/b&gt;")

    def test_yo(self):
        self.assertIn("<mark>", str(highlight("Ёжик", "еж")))
