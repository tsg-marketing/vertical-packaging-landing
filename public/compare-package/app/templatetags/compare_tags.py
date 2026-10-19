from django import template

from ..compare_utils import course_id

register = template.Library()


@register.filter
def compare_id(course):
    """Идентификатор курса для сравнения: "<school_slug>/<course_slug>"."""
    return course_id(course)


@register.simple_tag(takes_context=True)
def compare_url_without(context, course):
    """URL страницы сравнения без указанного курса (для крестика в шапке колонки)."""
    from django.urls import reverse

    from ..compare_utils import url_without

    ids = context.get("compare_ids_current") or []
    return url_without(reverse("compare"), ids, course_id(course))


@register.filter
def ru_plural(n, forms):
    """{{ 5|ru_plural:"курс,курса,курсов" }} -> "курсов"."""
    one, few, many = forms.split(",")
    n = abs(int(n))
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many
