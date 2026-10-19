from urllib.parse import unquote

COOKIE = "edukursy_compare"
MAX_COMPARE = 4


def parse_compare_ids(raw):
    """'a/b,c/d' -> ['a/b', 'c/d'] без дублей, не больше MAX_COMPARE."""
    result = []
    for part in unquote(raw or "").split(","):
        part = part.strip().strip("/")
        if part.count("/") == 1 and part not in result:
            result.append(part)
    return result[:MAX_COMPARE]


def compare(request):
    """Выбранные для сравнения курсы из cookie — чтобы кнопки рендерились сразу в нужном состоянии."""
    return {"compare_ids": parse_compare_ids(request.COOKIES.get(COOKIE, "")), "compare_max": MAX_COMPARE}
