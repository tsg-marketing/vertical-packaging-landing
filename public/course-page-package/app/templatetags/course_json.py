from django import template

from ..course_json import course_page_for

register = template.Library()


@register.simple_tag
def course_page(course, faqs=None):
    """{% load course_json %}{% course_page course faqs as cpage %} — если cpage не положили в контекст во view."""
    return course_page_for(course, faqs)
