"""
Два view:
  search_suggest — JSON для подсказок при вводе (GET /search/suggest/?q=...)
  search_page    — страница результатов (GET /search/?q=...), куда ведёт кнопка «Найти»

Модели Course / Profession — ваши. Проверьте функции *_to_dict: имена полей и картинок.
"""
from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count, Min, Q
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .models import Course, Profession
from .search_utils import MIN_CHARS, normalize, search

POPULAR = getattr(settings, "SEARCH_POPULAR", ["Python", "Дизайнер", "Аналитик данных", "Figma", "Маркетолог", "SQL"])
CACHE_SECONDS = 300


def professions_qs():
    return Profession.objects.annotate(
        courses_count=Count("courses", distinct=True),
        min_price_month=Min("courses__price_month"),
    )


def courses_qs():
    qs = Course.objects.select_related("school")
    if any(f.name == "is_active" for f in Course._meta.fields):
        qs = qs.filter(is_active=True)
    return qs


def _image_url(field):
    try:
        return field.url if field else None
    except ValueError:
        return None


def profession_to_dict(p):
    return {
        "name": p.name,
        "url": p.get_absolute_url(),
        "image": _image_url(getattr(p, "image", None)),
        "courses_count": getattr(p, "courses_count", 0) or 0,
        "min_price_month": getattr(p, "min_price_month", None),
    }


def course_to_dict(c):
    return {
        "name": c.name,
        "url": c.get_absolute_url(),
        "school": c.school.name,
        "school_logo": _image_url(getattr(c.school, "logo", None)),
        "price": c.price,
        "price_month": getattr(c, "price_month", None),
        "duration": getattr(c, "duration", None) or None,
    }


@require_GET
def search_suggest(request):
    q = request.GET.get("q", "")
    key = "suggest:" + normalize(q)
    data = cache.get(key)
    if data is None:
        r = search(professions_qs(), courses_qs(), q)
        data = {
            "query": q,
            "corrected": r["corrected"],
            "professions": [profession_to_dict(p) for p in r["professions"]],
            "courses": [course_to_dict(c) for c in r["courses"]],
            "total_professions": r["total_professions"],
            "total_courses": r["total_courses"],
            "popular": POPULAR,
        }
        cache.set(key, data, CACHE_SECONDS)
    resp = JsonResponse(data, json_dumps_params={"ensure_ascii": False})
    resp["Cache-Control"] = "public, max-age=60"
    resp["X-Robots-Tag"] = "noindex"
    return resp


@require_GET
def search_page(request):
    q = request.GET.get("q", "").strip()
    context = {"q": q, "popular": POPULAR, "min_chars": MIN_CHARS}
    if len(normalize(q)) >= MIN_CHARS:
        r = search(professions_qs(), courses_qs(), q, prof_limit=12, course_limit=10_000)
        page = Paginator(r["courses"], 24).get_page(request.GET.get("page"))
        context.update(
            professions=r["professions"],
            courses_page=page,
            total_professions=r["total_professions"],
            total_courses=r["total_courses"],
            corrected=r["corrected"],
        )
    return render(request, "edukursy/search/results.html", context)
