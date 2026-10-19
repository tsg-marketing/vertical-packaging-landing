from .compare_utils import COOKIE, parse_compare_ids


def compare(request):
    """Выбранные для сравнения курсы из cookie: кнопки «Сравнить» сразу рендерятся в нужном состоянии."""
    return {"compare_ids": parse_compare_ids(request.COOKIES.get(COOKIE, ""))}
