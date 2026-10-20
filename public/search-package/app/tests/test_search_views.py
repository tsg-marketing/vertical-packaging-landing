"""
Интеграционные тесты с БД. Перед запуском проверьте фабрики make_* под свои модели
(обязательные поля Course / School / Profession).
"""
from django.test import TestCase
from django.urls import reverse

from ..models import Course, Profession, School


def make_school(name="Школа 1", slug="school-1"):
    return School.objects.create(name=name, slug=slug)


def make_profession(name, slug):
    return Profession.objects.create(name=name, slug=slug)


def make_course(name, slug, school, profession, price=50000):
    return Course.objects.create(name=name, slug=slug, school=school, profession=profession, price=price)


class SuggestTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        s = make_school()
        dev = make_profession("Python-разработчик", "python-razrabotchik")
        des = make_profession("Дизайнер", "dizajner")
        make_course("Python с нуля", "python-s-nulya", s, dev)
        make_course("Автотесты на Python", "avtotesty", s, dev)
        make_course("Графический дизайнер", "graf", s, des)

    def get(self, q):
        return self.client.get(reverse("search_suggest"), {"q": q}).json()

    def test_course_and_profession(self):
        d = self.get("pyth")
        self.assertEqual([p["name"] for p in d["professions"]], ["Python-разработчик"])
        self.assertEqual(d["courses"][0]["name"], "Python с нуля")
        self.assertEqual(d["total_courses"], 2)

    def test_cyrillic_case_insensitive(self):
        self.assertEqual(self.get("ДИЗ")["total_professions"], 1)

    def test_wrong_layout(self):
        d = self.get("lbp")
        self.assertEqual(d["corrected"], "диз")
        self.assertEqual(d["total_professions"], 1)

    def test_short_query(self):
        d = self.get("p")
        self.assertEqual(d["courses"], [])

    def test_page(self):
        r = self.client.get(reverse("search"), {"q": "python"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Python с нуля")
