from types import SimpleNamespace as NS

from django.test import SimpleTestCase

from ..compare_utils import build_picks, build_rows, parse_compare_ids, url_with, url_without


def course(i, price, projects=None, rating=None):
    return NS(name=f"Курс {i}", slug=f"c{i}", price=price, projects_count=projects, school=NS(slug=f"s{i}", name=f"Школа {i}", rating=rating))


class ParseTests(SimpleTestCase):
    def test_no_limit(self):
        raw = ",".join(f"s{i}/c{i}" for i in range(25))
        self.assertEqual(len(parse_compare_ids(raw)), 25)

    def test_dedup_and_garbage(self):
        self.assertEqual(parse_compare_ids("a/b, a/b ,bad,,x/y/z,%2Fc%2Fd%2F"), ["a/b", "c/d"])

    def test_urls(self):
        self.assertEqual(url_without("/compare/", ["a/b", "c/d"], "a/b"), "/compare/?courses=c/d")
        self.assertEqual(url_without("/compare/", ["a/b"], "a/b"), "/compare/?courses=")
        self.assertEqual(url_with("/compare/", ["a/b"], "c/d"), "/compare/?courses=a/b,c/d")


class RowsTests(SimpleTestCase):
    specs = [{"title": "Цена", "rows": [
        {"label": "Цена", "get": lambda c: c.price, "best": "min"},
        {"label": "Проекты", "get": lambda c: c.projects_count, "best": "max"},
    ]}]

    def test_many_courses_best(self):
        cs = [course(i, 1000 + i * 10, projects=i) for i in range(10)]
        rows = build_rows(cs, self.specs)[0]["rows"]
        self.assertEqual([c["best"] for c in rows[0]["cells"]].index(True), 0)
        self.assertEqual([c["best"] for c in rows[1]["cells"]].index(True), 9)
        self.assertEqual(len(rows[0]["cells"]), 10)

    def test_equal_values_no_best(self):
        cs = [course(i, 500) for i in range(3)]
        cells = build_rows(cs, self.specs)[0]["rows"][0]["cells"]
        self.assertFalse(any(c["best"] for c in cells))

    def test_empty_row_hidden(self):
        cs = [course(i, 500) for i in range(3)]
        labels = [r["label"] for r in build_rows(cs, self.specs)[0]["rows"]]
        self.assertNotIn("Проекты", labels)

    def test_picks(self):
        cs = [course(1, 100, 3, 4.5), course(2, 200, 9, 4.9)]
        picks = build_picks(cs, price=lambda c: c.price, price_per_month=None, projects=lambda c: c.projects_count, rating=lambda c: c.school.rating)
        self.assertEqual([p["course"].name for p in picks], ["Курс 1", "Курс 2", "Курс 2"])
        self.assertEqual(build_picks(cs[:1], lambda c: 1, None, lambda c: 1, lambda c: 1), [])
