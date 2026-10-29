from django import template

from ..podborki_services import menu_tree

register = template.Library()


@register.inclusion_tag("edukursy/partials/podborki_menu.html", takes_context=True)
def podborki_menu(context):
    """{% load podborki_tags %}{% podborki_menu %} — пункт «Подборки курсов» с выпадающим деревом."""
    request = context.get("request")
    current = ""
    if request is not None and request.path.startswith("/podborki/"):
        current = request.path[len("/podborki/"):].strip("/")
    return {"tree": menu_tree(), "current": current, "request": request}


@register.filter
def ru_plural(n, forms):
    one, few, many = forms.split(",")
    n = abs(int(n or 0))
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


@register.filter
def startswith(value, prefix):
    return str(value or "").startswith(str(prefix or ""))
