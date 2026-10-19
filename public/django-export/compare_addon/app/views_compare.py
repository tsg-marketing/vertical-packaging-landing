"""
View страницы /compare/. Встроить в своё приложение (или взять логику в существующий view).
Модели Course / School — ваши; проверьте имена полей в ROW_SPECS.
"""
from django.shortcuts import redirect, render
from django.urls import reverse

from .compare_utils import (
    COOKIE,
    build_picks,
    build_rows,
    compare_state,
    ids_to_param,
    parse_compare_ids,
    resolve_courses,
    url_with,
)
from .models import Course


def rub(v):
    return f"{int(v):,}".replace(",", "\u00a0") + "\u00a0₽"


def per_month(c):
    months = getattr(c, "duration_months", None)
    return round(c.price / months) if c.price and months else None


ROW_SPECS = [
    {"title": "Стоимость", "rows": [
        {"label": "Полная цена", "get": lambda c: c.price, "fmt": rub, "best": "min"},
        {"label": "Цена без скидки", "get": lambda c: getattr(c, "old_price", None), "fmt": rub},
        {"label": "Рассрочка", "get": lambda c: getattr(c, "price_month", None), "fmt": lambda v: rub(v) + "/мес"},
        {"label": "Цена за месяц обучения", "get": per_month, "fmt": rub, "best": "min"},
        {"label": "Налоговый вычет", "get": lambda c: getattr(c, "tax_deduction", None) or getattr(c.school, "tax_deduction", None), "fmt": lambda v: "✓ 13%"},
    ]},
    {"title": "Длительность и формат", "rows": [
        {"label": "Длительность", "get": lambda c: getattr(c, "duration_months", None), "fmt": lambda v: f"{v} мес"},
        {"label": "Нагрузка", "get": lambda c: getattr(c, "hours_per_week", None)},
        {"label": "Формат", "get": lambda c: getattr(c, "format", None)},
        {"label": "Старт", "get": lambda c: getattr(c, "start_date", None)},
        {"label": "Бесплатный вводный урок", "get": lambda c: getattr(c, "free_lesson", None), "fmt": lambda v: "✓ Есть"},
    ]},
    {"title": "Обучение", "rows": [
        {"label": "Наставник", "get": lambda c: getattr(c, "mentor", None)},
        {"label": "Проверка заданий", "get": lambda c: getattr(c, "homework_review", None)},
        {"label": "Проектов в портфолио", "get": lambda c: getattr(c, "projects_count", None), "best": "max"},
        {"label": "Дипломный проект", "get": lambda c: getattr(c, "final_project", None), "fmt": lambda v: "✓ Есть"},
    ]},
    {"title": "Документ и гарантии", "rows": [
        {"label": "Документ об окончании", "get": lambda c: getattr(c, "certificate", None) or getattr(c.school, "certificate", None)},
        {"label": "Возврат денег", "get": lambda c: getattr(c.school, "refund", None)},
        {"label": "Рейтинг школы", "get": lambda c: getattr(c.school, "rating", None), "best": "max"},
    ]},
]


def compare_view(request):
    base = reverse("compare")
    raw = request.GET.get("courses")

    if raw is None:
        ids = parse_compare_ids(request.COOKIES.get(COOKIE, ""))
        if ids:
            return redirect(f"{base}?courses={ids_to_param(ids)}")

    ids = parse_compare_ids(raw)

    add = request.GET.get("add")
    if add:
        return redirect(url_with(base, ids, add.strip().strip("/")))

    courses = resolve_courses(Course, ids)
    ids = [f"{c.school.slug}/{c.slug}" for c in courses]

    groups = build_rows(courses, ROW_SPECS)
    if request.GET.get("diff") == "1" and len(courses) > 1:
        for g in groups:
            g["rows"] = [r for r in g["rows"] if not r["same"]]
        groups = [g for g in groups if g["rows"]]

    add_options = []
    if courses:
        add_options = (
            Course.objects.filter(profession=courses[0].profession)
            .exclude(pk__in=[c.pk for c in courses])
            .select_related("school")
            .order_by("-id")[:50]
        )

    context = {
        "courses": courses,
        "compare_ids_current": ids,
        "compare_state": compare_state(courses),
        "groups": groups,
        "picks": build_picks(
            courses,
            price=lambda c: c.price,
            price_per_month=per_month,
            projects=lambda c: getattr(c, "projects_count", None),
            rating=lambda c: getattr(c.school, "rating", None),
        ),
        "add_options": add_options,
        "diff": request.GET.get("diff") == "1",
        "colspan": len(courses) + 1,
    }
    return render(request, "edukursy/compare/compare.html", context)
