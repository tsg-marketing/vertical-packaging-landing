"""Необязательно: если меню собирается не тегом, а в base.html через контекст."""
from .podborki_services import menu_tree


def podborki(request):
    return {"podborki_tree": menu_tree()}
