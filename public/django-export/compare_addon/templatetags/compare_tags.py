from django import template

register = template.Library()


@register.filter
def compare_id(course):
    """Идентификатор курса для сравнения: "<school_slug>/<course_slug>"."""
    return f"{course.school.slug}/{course.slug}"
