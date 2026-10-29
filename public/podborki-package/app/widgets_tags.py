"""
Виджет «дерево с чекбоксами» для Course.tags (ManyToMany на CourseTag).
Выбранные — чипами сверху, поиск, развернуть/свернуть. Родители выбранных отмечаются «частично».
В базу пишется только то, что отмечено.
"""
from django import forms


class TagTreeWidget(forms.CheckboxSelectMultiple):
    """
    Шаблон лежит в <app>/templates/podborki/widgets/. Рендерится через django.template.loader,
    поэтому работает без настройки FORM_RENDERER.
    """

    template_name = "podborki/widgets/tag_tree.html"

    def render(self, name, value, attrs=None, renderer=None):
        from django.template.loader import render_to_string
        from django.utils.safestring import mark_safe

        return mark_safe(render_to_string(self.template_name, self.get_context(name, value, attrs)))

    class Media:
        css = {"all": ("admin/podborki/podborki-admin.css",)}
        js = ("admin/podborki/tag-tree.js",)

    def get_context(self, name, value, attrs):
        from .admin_tags import tree_ordered
        from .podborki_services import admin_counts

        ctx = super().get_context(name, value, attrs)
        selected = {str(v) for v in (value or [])}
        tags = tree_ordered()
        counts = admin_counts()
        by_parent = {}
        by_id = {t.pk: t for t in tags}
        for t in tags:
            by_parent.setdefault(t.parent_id, []).append(t)

        def path_of(t):
            names = []
            while t is not None:
                names.insert(0, t.display_name)
                t = by_id.get(t.parent_id)
            return " › ".join(names)

        def build(pid):
            out = []
            for t in by_parent.get(pid, []):
                kids = build(t.pk)
                checked = str(t.pk) in selected
                partial = not checked and any(k["checked"] or k["partial"] for k in kids)
                out.append({
                    "id": t.pk, "name": t.name, "short": t.display_name, "level": t.level,
                    "active": t.is_active, "checked": checked, "partial": partial,
                    "count": counts.get(t.pk, (0, 0))[1], "children": kids,
                    "path": path_of(t),
                })
            return out

        ctx["widget"]["tree"] = build(None)
        ctx["widget"]["selected_items"] = [{"pk": t.pk, "path": path_of(t)} for t in tags if str(t.pk) in selected]
        return ctx
