"""
Сравнение курсов без ограничения по количеству.

Идентификатор курса: "<school_slug>/<course_slug>".
Список приходит из GET ?courses=a/b,c/d или из cookie edukursy_compare.
"""
from urllib.parse import unquote

COOKIE = "edukursy_compare"
URL_SOFT_LIMIT = 1800


def parse_compare_ids(raw):
    """'a/b,c/d,a/b' -> ['a/b', 'c/d']: без дублей, порядок сохраняется, без ограничения по количеству."""
    result = []
    seen = set()
    for part in unquote(raw or "").split(","):
        part = part.strip().strip("/")
        if part.count("/") != 1 or part in seen:
            continue
        seen.add(part)
        result.append(part)
    return result


def ids_to_param(ids):
    return ",".join(ids)


def url_without(base_url, ids, remove_id):
    rest = [i for i in ids if i != remove_id]
    return f"{base_url}?courses={ids_to_param(rest)}"


def url_with(base_url, ids, add_id):
    if add_id in ids:
        return f"{base_url}?courses={ids_to_param(ids)}"
    return f"{base_url}?courses={ids_to_param(ids + [add_id])}"


def course_id(course):
    return f"{course.school.slug}/{course.slug}"


def resolve_courses(Course, ids):
    """Один SQL-запрос на любое количество курсов. Порядок — как в ids. Несуществующие пропускаются."""
    if not ids:
        return []
    by_school = {}
    for cid in ids:
        school_slug, course_slug = cid.split("/")
        by_school.setdefault(school_slug, []).append(course_slug)
    from django.db.models import Q

    q = Q()
    for school_slug, slugs in by_school.items():
        q |= Q(school__slug=school_slug, slug__in=slugs)
    found = {course_id(c): c for c in Course.objects.filter(q).select_related("school")}
    return [found[cid] for cid in ids if cid in found]


def compare_state(courses):
    return [{"id": course_id(c), "name": c.name, "school": c.school.name} for c in courses]


def _empty(v):
    return v is None or v is False or v == ""


def _best(values, mode):
    present = [v for v in values if not _empty(v)]
    if len(present) < 2 or len(set(present)) == 1:
        return set()
    target = min(present) if mode == "min" else max(present)
    return {i for i, v in enumerate(values) if v == target}


def build_rows(courses, row_specs):
    """
    row_specs: список групп
      [{"title": "Стоимость", "rows": [
          {"label": "Полная цена", "get": lambda c: c.price, "fmt": rub, "best": "min"}, ...]}]
    Возвращает группы со строками; у каждой строки: label, cells [{value, text, best}], same (все значения одинаковые).
    Работает для любого числа курсов.
    """
    groups = []
    for group in row_specs:
        rows = []
        for spec in group["rows"]:
            raw = [spec["get"](c) for c in courses]
            best = _best(raw, spec["best"]) if spec.get("best") else set()
            fmt = spec.get("fmt") or (lambda v: v)
            cells = [{"value": v, "text": (None if _empty(v) else fmt(v)), "best": i in best} for i, v in enumerate(raw)]
            if all(cell["text"] is None for cell in cells):
                continue
            rows.append({"label": spec["label"], "cells": cells, "same": len({str(v) for v in raw}) <= 1})
        if rows:
            groups.append({"title": group["title"], "rows": rows})
    return groups


def build_picks(courses, price, price_per_month, projects, rating):
    """
    Итоговые карточки «Коротко: какой курс выбрать». Каждая — только если есть данные и есть разница.
    price / price_per_month / projects / rating — функции course -> число или None.
    """
    if len(courses) < 2:
        return []
    picks = []
    specs = [
        ("💰", "Дешевле всего", price, "min"),
        ("🎓", "Больше всего практики", projects, "max"),
        ("⭐", "Выше рейтинг школы", rating, "max"),
    ]
    for icon, label, getter, mode in specs:
        values = [getter(c) for c in courses]
        best = _best(values, mode)
        if len(best) == 1:
            picks.append({"icon": icon, "label": label, "course": courses[next(iter(best))]})
    return picks
