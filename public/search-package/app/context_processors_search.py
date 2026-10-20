import json

from django.conf import settings

DEFAULT = ["Python", "Дизайнер", "Аналитик данных", "Figma", "Маркетолог", "SQL"]


def search_popular(request):
    """«Часто ищут» в подсказках. Список меняется в settings.SEARCH_POPULAR."""
    items = getattr(settings, "SEARCH_POPULAR", DEFAULT)
    return {"search_popular": items, "search_popular_json": json.dumps(items, ensure_ascii=False)}
