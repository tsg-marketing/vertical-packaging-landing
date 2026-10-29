"""
Страницы подборок:
  /podborki/                       — все подборки деревом
  /podborki/<путь>/                — курсы подборки и всех вложенных, до 3 сегментов пути
"""
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .models import CourseTag
from .podborki_services import build_tree, courses_for_tag, find_node

PER_PAGE = 24
SORTS = {
    "popular": None,
    "price_asc": "price",
    "price_desc": "-price",
    "new": "-id",
}


def Course_default_order(qs):
    """«Популярные»: по полю популярности, если есть, иначе — новые сверху."""
    names = {f.name for f in qs.model._meta.get_fields()}
    for field in ("popularity", "rating", "reviews_count", "views"):
        if field in names:
            return (f"-{field}", "-id")
    return ("-id",)


def podborki_index(request):
    return render(request, "edukursy/podborki/index.html", {"tree": build_tree()})


def podborka_detail(request, path):
    path = path.strip("/")
    if path.count("/") > 2:
        raise Http404
    tag = get_object_or_404(CourseTag.objects.select_related("parent__parent"), full_path=path, is_active=True)
    for a in tag.ancestors():
        if not a.is_active:
            raise Http404

    qs = courses_for_tag(tag).select_related("school")
    sort = request.GET.get("sort", "popular")
    if sort not in SORTS:
        sort = "popular"
    order = SORTS[sort]
    qs = qs.order_by(order, "id") if order else qs.order_by(*(Course_default_order(qs)))
    page = Paginator(qs, PER_PAGE).get_page(request.GET.get("page"))

    node = find_node(tag.full_path)
    children = node.children if node else []
    siblings, parent_node = [], None
    if not children and tag.parent_id:
        parent_node = find_node(tag.parent.full_path)
        siblings = parent_node.children if parent_node else []

    return render(request, "edukursy/podborki/detail.html", {
        "tag": tag,
        "node": node,
        "ancestors": tag.ancestors(),
        "children": children,
        "siblings": siblings,
        "parent_node": parent_node,
        "page_obj": page,
        "total": page.paginator.count,
        "sort": sort,
    })
