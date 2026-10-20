import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def highlight(text, query):
    """{{ course.name|highlight:q }} — подсвечивает слова запроса тегом <mark>. Безопасно экранирует."""
    text = str(text or "")
    ws = sorted({w for w in re.split(r"\s+", (query or "").lower().replace("ё", "е")) if len(w) >= 2}, key=len, reverse=True)
    if not ws:
        return escape(text)
    norm = text.lower().replace("ё", "е")
    marks = []
    for w in ws:
        start = 0
        while (i := norm.find(w, start)) > -1:
            marks.append((i, i + len(w)))
            start = i + len(w)
    marks.sort()
    out, pos = [], 0
    for a, b in marks:
        if a < pos:
            continue
        out.append(escape(text[pos:a]))
        out.append("<mark>" + escape(text[a:b]) + "</mark>")
        pos = b
    out.append(escape(text[pos:]))
    return mark_safe("".join(out))
