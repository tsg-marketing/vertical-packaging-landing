"""
Поиск по названию курса и профессии + подсказки при вводе.

Работает на PostgreSQL и SQLite. В SQLite поиск без учёта регистра по кириллице НЕ работает
(LIKE понимает регистр только для латиницы), поэтому, если у модели есть поле search_text
(название в нижнем регистре, ё→е), поиск идёт по нему. См. models_mixin.py.
"""
import re

from django.db.models import Case, IntegerField, Q, Value, When

MIN_CHARS = 2
MAX_QUERY = 100
SUGGEST_PROFESSIONS = 4
SUGGEST_COURSES = 6

EN = "qwertyuiop[]asdfghjkl;'zxcvbnm,.`"
RU = "йцукенгшщзхъфывапролджэячсмитьбюё"
_EN2RU = {e: r for e, r in zip(EN, RU)}
_RU2EN = {r: e for e, r in zip(EN, RU)}


def normalize(text):
    """'  Python  Ёлка ' -> 'python елка'."""
    text = (text or "")[:MAX_QUERY].lower().replace("ё", "е")
    text = re.sub(r"[^\w\s+#.-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def swap_layout(text):
    """Неверная раскладка: 'ghjuh' -> 'прогр', 'зн' -> 'py'."""
    return "".join(_EN2RU.get(ch, _RU2EN.get(ch, ch)) for ch in text.lower())


def words(query):
    return [w for w in normalize(query).split(" ") if w][:5]


def _field(model):
    names = {f.name for f in model._meta.get_fields()}
    return "search_text" if "search_text" in names else "name"


def filter_by_words(qs, query):
    """Все слова запроса должны встретиться в названии. Ранг: 0 — с начала, 1 — с начала слова, 2 — в середине."""
    ws = words(query)
    if not ws:
        return qs.none()
    field = _field(qs.model)
    lookup = "contains" if field == "search_text" else "icontains"
    cond = Q()
    for w in ws:
        cond &= Q(**{f"{field}__{lookup}": w})
    first = ws[0]
    start = "startswith" if field == "search_text" else "istartswith"
    return qs.filter(cond).annotate(
        search_rank=Case(
            When(**{f"{field}__{start}": first}, then=Value(0)),
            When(**{f"{field}__{lookup}": " " + first}, then=Value(1)),
            When(**{f"{field}__{lookup}": "-" + first}, then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    )


def search(professions_qs, courses_qs, query, prof_limit=SUGGEST_PROFESSIONS, course_limit=SUGGEST_COURSES):
    """
    Возвращает dict: professions, courses, total_professions, total_courses, corrected (или None).
    Если ничего не нашлось — пробует запрос в другой раскладке.
    """

    def run(q):
        p = filter_by_words(professions_qs, q)
        c = filter_by_words(courses_qs, q)
        p_total, c_total = p.count(), c.count()
        return {
            "professions": list(p.order_by("search_rank", "name")[:prof_limit]) if p_total else [],
            "courses": list(c.order_by("search_rank", "name")[:course_limit]) if c_total else [],
            "total_professions": p_total,
            "total_courses": c_total,
            "corrected": None,
        }

    if len(normalize(query)) < MIN_CHARS:
        return {"professions": [], "courses": [], "total_professions": 0, "total_courses": 0, "corrected": None}

    result = run(query)
    if not result["total_professions"] and not result["total_courses"]:
        alt = swap_layout(normalize(query))
        if alt != normalize(query):
            alt_result = run(alt)
            if alt_result["total_professions"] or alt_result["total_courses"]:
                alt_result["corrected"] = alt
                return alt_result
    return result
