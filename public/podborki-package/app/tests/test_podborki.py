"""
Тесты подборок. Перед запуском поправьте make_course под обязательные поля вашей модели Course.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from ..models import Course, CourseTag, School


def make_course(name, **extra):
    school = School.objects.first() or School.objects.create(name="Школа 1", slug="school-1")
    return Course.objects.create(name=name, slug=name.lower().replace(" ", "-"), school=school, price=10000, **extra)


class TreeTests(TestCase):
    def setUp(self):
        self.root = CourseTag.objects.create(name="Курсы с трудоустройством", slug="job")
        self.l2 = CourseTag.objects.create(name="Сразу", slug="now", parent=self.root)
        self.l3 = CourseTag.objects.create(name="В IT", slug="it", parent=self.l2)

    def test_paths_and_levels(self):
        self.assertEqual(self.l3.full_path, "job/now/it")
        self.assertEqual(self.l3.level, 2)
        self.assertEqual(self.l3.get_absolute_url(), "/podborki/job/now/it/")

    def test_max_depth(self):
        t = CourseTag(name="4-й", slug="four", parent=self.l3)
        with self.assertRaises(ValidationError):
            t.full_clean()

    def test_move_subtree_too_deep(self):
        other = CourseTag.objects.create(name="Другая", slug="other")
        other2 = CourseTag.objects.create(name="Другая 2", slug="o2", parent=other)
        self.l2.parent = other2
        with self.assertRaises(ValidationError):
            self.l2.full_clean()

    def test_no_cycle(self):
        self.root.parent = self.l3
        with self.assertRaises(ValidationError):
            self.root.full_clean()

    def test_unique_slug_in_parent(self):
        t = CourseTag(name="Ещё", slug="now", parent=self.root)
        with self.assertRaises(ValidationError):
            t.full_clean()
        other = CourseTag.objects.create(name="Другая", slug="other")
        CourseTag(name="Можно", slug="now", parent=other).full_clean()

    def test_rename_updates_children_paths(self):
        self.root.slug = "rabota"
        self.root.save()
        self.l3.refresh_from_db()
        self.assertEqual(self.l3.full_path, "rabota/now/it")


class DeleteTests(TestCase):
    def setUp(self):
        self.root = CourseTag.objects.create(name="Root", slug="root")
        self.leaf = CourseTag.objects.create(name="Leaf", slug="leaf", parent=self.root)
        self.empty = CourseTag.objects.create(name="Empty", slug="empty")

    def test_cannot_delete_with_children(self):
        with self.assertRaises((ValidationError, ProtectedError)):
            self.root.delete()

    def test_cannot_delete_with_courses(self):
        c = make_course("Python")
        c.tags.add(self.leaf)
        with self.assertRaises((ValidationError, ProtectedError)):
            self.leaf.delete()
        with self.assertRaises(ProtectedError), transaction.atomic():
            CourseTag.objects.filter(pk=self.leaf.pk).delete()
        self.assertTrue(CourseTag.objects.filter(pk=self.leaf.pk).exists())

    def test_can_delete_empty(self):
        self.empty.delete()
        self.assertFalse(CourseTag.objects.filter(slug="empty").exists())


class PagesTests(TestCase):
    def setUp(self):
        self.root = CourseTag.objects.create(name="Для детей", menu_name="Для детей", slug="kids")
        self.l2 = CourseTag.objects.create(name="7–10 лет", slug="7-10", parent=self.root)
        self.l3 = CourseTag.objects.create(name="Программирование", slug="prog", parent=self.l2)
        self.hidden = CourseTag.objects.create(name="Скрытая", slug="hidden", is_active=False)
        self.c1 = make_course("Scratch")
        self.c1.tags.add(self.l3)
        self.c2 = make_course("Roblox")
        self.c2.tags.add(self.l2, self.l3)

    def test_parent_shows_children_courses_without_duplicates(self):
        r = self.client.get("/podborki/kids/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["total"], 2)
        self.assertContains(r, "Scratch")

    def test_leaf(self):
        r = self.client.get("/podborki/kids/7-10/prog/")
        self.assertEqual(r.context["total"], 2)

    def test_hidden_404(self):
        self.assertEqual(self.client.get("/podborki/hidden/").status_code, 404)
        self.root.is_active = False
        self.root.save()
        self.assertEqual(self.client.get("/podborki/kids/7-10/").status_code, 404)

    def test_index_and_menu(self):
        r = self.client.get("/podborki/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Для детей")
        self.assertNotContains(r, "Скрытая")

    def test_menu_query_count_is_constant(self):
        from django.core.cache import cache

        from ..podborki_services import build_tree

        cache.clear()
        with self.assertNumQueries(2):
            build_tree()
        with self.assertNumQueries(0):
            build_tree()


class AdminTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("admin", "a@a.ru", "pass")
        self.client.force_login(self.admin)
        self.root = CourseTag.objects.create(name="Root", slug="root")
        self.a = CourseTag.objects.create(name="A", slug="a", parent=self.root, order=10)
        self.b = CourseTag.objects.create(name="B", slug="b", parent=self.root, order=20)
        o = CourseTag._meta
        self.prefix = f"admin:{o.app_label}_{o.model_name}"

    def test_changelist(self):
        r = self.client.get(reverse(f"{self.prefix}_changelist"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "ур. 2")

    def test_reorder(self):
        r = self.client.post(reverse(f"{self.prefix}_reorder"), data=f'{{"parent": {self.root.pk}, "ids": [{self.b.pk}, {self.a.pk}]}}', content_type="application/json")
        self.assertEqual(r.status_code, 200)
        self.a.refresh_from_db()
        self.b.refresh_from_db()
        self.assertLess(self.b.order, self.a.order)

    def test_reorder_rejects_other_level(self):
        r = self.client.post(reverse(f"{self.prefix}_reorder"), data=f'{{"parent": null, "ids": [{self.a.pk}]}}', content_type="application/json")
        self.assertEqual(r.status_code, 400)

    def test_delete_blocked_page(self):
        r = self.client.get(reverse(f"{self.prefix}_delete", args=[self.root.pk]))
        self.assertContains(r, "Удалить нельзя")

    def test_bulk_delete_skips_used(self):
        r = self.client.post(reverse(f"{self.prefix}_changelist"), {"action": "safe_delete", "_selected_action": [self.root.pk, self.a.pk]}, follow=True)
        self.assertFalse(CourseTag.objects.filter(pk=self.a.pk).exists())
        self.assertTrue(CourseTag.objects.filter(pk=self.root.pk).exists())
