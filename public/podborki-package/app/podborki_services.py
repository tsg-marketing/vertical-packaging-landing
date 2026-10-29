"""
Дерево подборок для меню и страниц. Один запрос на всё дерево + кэш.

Число курсов в подборке = курсы этой подборки И всех вложенных (без дублей).
Так посетитель, открыв «Курсы с трудоустройством», видит всё, что лежит в «Сразу › В IT» и т.д.
"""
from collections import defaultdict

from django.apps import apps
from django.core.cache import cache
from django.db.models import Count

MENU_CACHE_KEY = "podborki:tree:v1"
MENU_CACHE_SECONDS = 600


def _models():
    CourseTag = apps.get_model(*_tag_model_label().split("."))
    Course = CourseTag._meta.get_field("courses").related_model
    return CourseTag, Course


def _tag_model_label():
    from django.conf import settings

    return getattr(settings, "PODBORKI_TAG_MODEL", "catalog.CourseTag")


def visible_courses(Course):
    qs = Course.objects.all()
    names = {f.name for f in Course._meta.get_fields()}
    if "is_active" in names:
        qs = qs.filter(is_active=True)
    return qs


def invalidate_menu_cache():
    cache.delete(MENU_CACHE_KEY)


class Node:
    __slots__ = ("id", "name", "menu_name", "slug", "full_path", "level", "icon", "url", "show_in_menu", "children", "count", "parent_id", "description")

    def __init__(self, tag):
        self.id = tag.id
        self.name = tag.name
        self.menu_name = tag.menu_name or tag.name
        self.slug = tag.slug
        self.full_path = tag.full_path
        self.level = tag.level
        self.icon = tag.icon
        self.url = tag.get_absolute_url()
        self.show_in_menu = tag.show_in_menu
        self.parent_id = tag.parent_id
        self.description = tag.description
        self.children = []
        self.count = 0


def build_tree(use_cache=True):
    """
    Список корневых Node (только активные, по order). У каждого .children и .count.
    Подборка с неактивным родителем тоже скрывается.
    """
    if use_cache:
        cached = cache.get(MENU_CACHE_KEY)
        if cached is not None:
            return cached
    CourseTag, Course = _models()
    tags = list(CourseTag.objects.filter(is_active=True).order_by("level", "order", "name"))
    nodes = {t.id: Node(t) for t in tags}
    roots = []
    for t in tags:
        n = nodes[t.id]
        if t.parent_id is None:
            roots.append(n)
        elif t.parent_id in nodes:
            nodes[t.parent_id].children.append(n)

    through = Course.tags.through
    tag_fk = [f.name for f in through._meta.fields if f.related_model is CourseTag][0]
    course_fk = [f.name for f in through._meta.fields if f.related_model is Course][0]
    rows = through.objects.filter(**{f"{tag_fk}__in": list(nodes), f"{course_fk}__in": visible_courses(Course)}).values_list(f"{tag_fk}_id", f"{course_fk}_id")
    direct = defaultdict(set)
    for tag_id, course_id in rows:
        direct[tag_id].add(course_id)

    def fill(node):
        ids = set(direct.get(node.id, ()))
        for ch in node.children:
            ids |= fill(ch)
        node.count = len(ids)
        return ids

    for r in roots:
        fill(r)
    if use_cache:
        cache.set(MENU_CACHE_KEY, roots, MENU_CACHE_SECONDS)
    return roots


def menu_tree():
    """Для меню: только show_in_menu, пустые подборки скрываются (count == 0)."""

    def keep(nodes):
        out = []
        for n in nodes:
            if not n.show_in_menu or n.count == 0:
                continue
            copy = Node.__new__(Node)
            for s in Node.__slots__:
                setattr(copy, s, getattr(n, s))
            copy.children = keep(n.children)
            out.append(copy)
        return out

    return keep(build_tree())


def find_node(path):
    def walk(nodes):
        for n in nodes:
            if n.full_path == path:
                return n
            if path.startswith(n.full_path + "/"):
                found = walk(n.children)
                if found:
                    return found
        return None

    return walk(build_tree())


def courses_for_tag(tag):
    """Курсы подборки и всех вложенных, без дублей."""
    CourseTag, Course = _models()
    ids = tag.descendant_ids(include_self=True)
    active_ids = list(CourseTag.objects.filter(id__in=ids, is_active=True).values_list("id", flat=True))
    return visible_courses(Course).filter(tags__in=active_ids).distinct()


def admin_counts():
    """Для списка в админке: {tag_id: (напрямую, всего с вложенными)} — 2 запроса на всё дерево."""
    CourseTag, Course = _models()
    tags = list(CourseTag.objects.values("id", "parent_id"))
    direct_qs = CourseTag.objects.annotate(n=Count("courses", distinct=True)).values_list("id", "n")
    direct_n = dict(direct_qs)
    through = Course.tags.through
    tag_fk = [f.name for f in through._meta.fields if f.related_model is CourseTag][0]
    course_fk = [f.name for f in through._meta.fields if f.related_model is Course][0]
    sets = defaultdict(set)
    for t, c in through.objects.values_list(f"{tag_fk}_id", f"{course_fk}_id"):
        sets[t].add(c)
    children = defaultdict(list)
    for t in tags:
        children[t["parent_id"]].append(t["id"])

    total = {}

    def fill(tid):
        s = set(sets.get(tid, ()))
        for ch in children.get(tid, ()):
            s |= fill(ch)
        total[tid] = len(s)
        return s

    for root in children.get(None, ()):
        fill(root)
    return {t["id"]: (direct_n.get(t["id"], 0), total.get(t["id"], 0)) for t in tags}
