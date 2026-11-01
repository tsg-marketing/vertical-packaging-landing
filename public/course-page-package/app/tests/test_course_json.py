"""Тесты сборки блоков из JSON — без базы данных."""
import json
from pathlib import Path

from django.test import SimpleTestCase

from ..course_json import build_course_page, parse_json, validate_editorial, validate_extract

SAMPLES = Path(__file__).resolve().parent / "samples"


def load(name):
    return json.loads((SAMPLES / name).read_text(encoding="utf-8"))


class ParseTests(SimpleTestCase):
    def test_fenced(self):
        self.assertEqual(parse_json('```json\n{"a": 1}\n```'), {"a": 1})

    def test_empty(self):
        for v in (None, "", "  ", {}, "null"):
            self.assertEqual(parse_json(v), {})

    def test_not_object(self):
        with self.assertRaises(ValueError):
            parse_json("[1, 2]")


class BuildTests(SimpleTestCase):
    def test_full(self):
        p = build_course_page(extract=load("extract_full.json"), editorial=load("editorial_full.json"))
        self.assertTrue(p.lead.startswith("Длинная онлайн-программа"))
        self.assertEqual(p.lead_source, "editorial_intro")
        self.assertTrue(p.summary.startswith("Курс рассчитан"))
        self.assertEqual(len(p.learn), 8)
        self.assertEqual([f.key for f in p.facts], ["level", "format", "duration", "certificate", "employment"])
        self.assertEqual(len(p.for_whom), 2, "берётся вариант редакции")
        self.assertEqual(len(p.check), 4)
        self.assertTrue(p.verdict.startswith("Хороший вариант"))
        self.assertEqual(len(p.faq), 7)
        self.assertEqual(len(p.source_facts), 6)
        self.assertEqual(p.source_domain, "school-1.ru")
        self.assertFalse(p.is_empty)

    def test_missing_keys_skip_blocks(self):
        p = build_course_page(extract={"course_title": "X", "what_you_learn": ["SQL"]}, editorial={})
        self.assertEqual(p.learn, ["SQL"])
        for attr in ("lead", "summary", "verdict", "price_text"):
            self.assertEqual(getattr(p, attr), "")
        for attr in ("facts", "for_whom", "not_for_whom", "features", "pros", "cons", "check", "faq", "source_facts", "prerequisites"):
            self.assertEqual(getattr(p, attr), [], attr)

    def test_null_and_empty_values_skip(self):
        p = build_course_page(extract={"short_summary": "  ", "pros": [], "level": None, "certificate": None, "source_facts": {"pricing_excerpt": None}}, editorial=None)
        self.assertTrue(p.is_empty)

    def test_false_is_shown(self):
        p = build_course_page(extract={"employment_support": False, "certificate": "false"}, editorial={})
        self.assertEqual([(f.key, f.value) for f in p.facts], [("certificate", "Не выдаётся"), ("employment", "Помощь не заявлена")])

    def test_failed_ignored(self):
        p = build_course_page(extract={"extraction_status": "failed", "what_you_learn": ["X"]}, editorial={"draft_status": "ok", "pros": ["A"]})
        self.assertEqual(p.learn, [])
        self.assertEqual(p.pros, ["A"])

    def test_extract_fallback(self):
        p = build_course_page(extract=load("extract_full.json"), editorial={})
        self.assertEqual(p.lead_source, "short_summary")
        self.assertEqual(p.summary, "", "short_summary не повторяется дважды")
        self.assertEqual(len(p.for_whom), 3)
        self.assertEqual(p.verdict_source, "extract.editorial_verdict")

    def test_faq_dedup_with_admin(self):
        p = build_course_page(extract=load("extract_full.json"), editorial=load("editorial_full.json"), skip_questions=["Нужен ли опыт программирования?"])
        self.assertNotIn("Нужен ли опыт программирования?", [f["question"] for f in p.faq])

    def test_bad_types_do_not_crash(self):
        p = build_course_page(extract={"what_you_learn": "строка", "faq": [{"question": "Q"}], "format": ["tv", "online"], "level": "pro"}, editorial={"pros": [1, "Ок"]})
        self.assertEqual(p.learn, [])
        self.assertEqual(p.faq, [])
        self.assertEqual(p.formats, ["Онлайн"])
        self.assertEqual(p.level, "")
        self.assertEqual(p.pros, ["Ок"])

    def test_broken_json_string(self):
        p = build_course_page(extract='{"a": ', editorial="")
        self.assertTrue(p.is_empty)

    def test_partial_samples(self):
        p = build_course_page(extract=load("extract_partial.json"), editorial=load("editorial_partial.json"))
        self.assertEqual(p.learn[0], "SELECT, WHERE, ORDER BY")
        self.assertEqual([f.key for f in p.facts], ["format", "duration", "employment"])
        self.assertEqual(p.check, ["Уточнить, будет ли проверка заданий"])
        self.assertEqual(p.verdict, "")


class ValidateTests(SimpleTestCase):
    def test_samples_valid(self):
        for name, fn in (("extract_full.json", validate_extract), ("editorial_full.json", validate_editorial), ("extract_partial.json", validate_extract)):
            errors, _ = fn(load(name))
            self.assertEqual(errors, [], name)

    def test_errors(self):
        errors, _ = validate_extract({"certificate": "да", "format": ["tv"], "level": "pro", "faq": [{"question": "Q"}], "pros": "x"})
        self.assertEqual(len(errors), 5)

    def test_warnings(self):
        errors, warnings = validate_editorial({"draft_status": "ok", "extra": 1})
        self.assertEqual(errors, [])
        self.assertTrue(any("extra" in w for w in warnings))
        self.assertTrue(any("нет ключей" in w for w in warnings))
