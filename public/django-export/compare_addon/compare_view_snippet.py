"""
Фрагмент для view страницы /compare/. Встроить в существующий CompareView.

Источник списка курсов (по приоритету):
1) GET ?courses=school/course,school/course — ссылка, которой можно поделиться;
2) cookie edukursy_compare — если параметра нет (пользователь нажал «Сравнения» в меню).
"""
from django.db.models import Q
from django.shortcuts import redirect

from .context_processors import COOKIE, parse_compare_ids


def resolve_compare_courses(request, Course):
    raw = request.GET.get("courses")
    ids = parse_compare_ids(raw if raw is not None else request.COOKIES.get(COOKIE, ""))
    if not ids:
        return [], []
    q = Q()
    for cid in ids:
        school_slug, course_slug = cid.split("/")
        q |= Q(school__slug=school_slug, slug=course_slug)
    found = {f"{c.school.slug}/{c.slug}": c for c in Course.objects.filter(q).select_related("school")}
    courses = [found[cid] for cid in ids if cid in found]
    state = [{"id": f"{c.school.slug}/{c.slug}", "name": c.name, "school": c.school.name} for c in courses]
    return courses, state


# Пример внутри view:
#
# def compare_view(request):
#     if "courses" not in request.GET and request.COOKIES.get(COOKIE):
#         ids = parse_compare_ids(request.COOKIES[COOKIE])
#         if ids:
#             return redirect(f"{request.path}?courses={','.join(ids)}")
#     courses, state = resolve_compare_courses(request, Course)
#     context = {"courses": courses, "compare_state": state, ...}
