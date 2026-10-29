"""
Админка подборок.

- Список CourseTag деревом: отступы, уровень, «Курсов» (напрямую) и «Всего» (с вложенными),
  переключатели «Активна»/«В меню» прямо в списке, порядок перетаскиванием и стрелками.
- Удаление: только если нет курсов и вложенных подборок. Замок с причиной в списке,
  своя страница «Удалить нельзя», массовое удаление пропускает занятые подборки.
- Форма: родитель — только 1-й и 2-й уровень, без себя и своих вложенных.
- CourseAdmin: поле tags виджетом-деревом, колонка «Подборки», фильтр по подборке
  (с вложенными) и действия «Добавить в подборку / Убрать из подборки».

Подключение: см. PROMPT.md, шаг «Админка».
"""
import json

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Case, IntegerField, ProtectedError, Value, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join

from .models import CourseTag
from .models_tags import MAX_DEPTH
from .podborki_services import admin_counts, invalidate_menu_cache
from .widgets_tags import TagTreeWidget


def tag_url(action, *args):
    o = CourseTag._meta
    return reverse(f"admin:{o.app_label}_{o.model_name}_{action}", args=args)


def course_list_url(tag_id=None):
    o = CourseTag._meta.get_field("courses").related_model._meta
    url = reverse(f"admin:{o.app_label}_{o.model_name}_changelist")
    return f"{url}?podborka={tag_id}" if tag_id else url


def tree_ordered(qs=None):
    """Подборки в порядке дерева: родитель, затем его дети по order."""
    tags = list((qs if qs is not None else CourseTag.objects.all()).select_related("parent").order_by("level", "order", "name"))
    by_parent = {}
    for t in tags:
        by_parent.setdefault(t.parent_id, []).append(t)
    out = []

    def walk(pid):
        for t in by_parent.get(pid, []):
            out.append(t)
            walk(t.pk)

    walk(None)
    seen = {t.pk for t in out}
    out += [t for t in tags if t.pk not in seen]
    return out


class CourseTagForm(forms.ModelForm):
    class Meta:
        model = CourseTag
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = CourseTag.objects.filter(level__lt=MAX_DEPTH - 1)
        if self.instance.pk:
            qs = qs.exclude(pk__in=self.instance.descendant_ids(include_self=True))
        self.fields["parent"].queryset = qs
        self.fields["parent"].label_from_instance = lambda t: ("— " * t.level) + t.name
        self.fields["parent"].choices = [("", "— Нет (1-й уровень) —")] + [(t.pk, ("— " * t.level) + t.name) for t in tree_ordered(qs)]
        self.fields["slug"].required = False


class LevelFilter(admin.SimpleListFilter):
    title = "уровень"
    parameter_name = "level"

    def lookups(self, request, model_admin):
        return [(str(i), f"{i + 1}-й") for i in range(MAX_DEPTH)]

    def queryset(self, request, qs):
        return qs.filter(level=int(self.value())) if self.value() else qs


class HasCoursesFilter(admin.SimpleListFilter):
    title = "курсы"
    parameter_name = "has_courses"

    def lookups(self, request, model_admin):
        return [("no", "Без курсов"), ("yes", "С курсами")]

    def queryset(self, request, qs):
        if self.value() == "no":
            return qs.filter(courses__isnull=True)
        if self.value() == "yes":
            return qs.filter(courses__isnull=False).distinct()
        return qs


@admin.register(CourseTag)
class CourseTagAdmin(admin.ModelAdmin):
    form = CourseTagForm
    change_list_template = "admin/podborki/coursetag/change_list.html"
    delete_confirmation_template = "admin/podborki/coursetag/delete_confirmation.html"
    list_display = ("drag", "tree_name", "direct_col", "total_col", "is_active", "show_in_menu", "order_col", "actions_col")
    list_display_links = None
    list_editable = ("is_active", "show_in_menu")
    list_filter = (LevelFilter, "is_active", "show_in_menu", HasCoursesFilter)
    search_fields = ("name", "menu_name", "slug", "full_path")
    list_per_page = 500
    actions = ["safe_delete", "make_active", "make_hidden", "add_to_menu", "remove_from_menu"]
    readonly_fields = ("full_path_link", "courses_info")
    fieldsets = (
        ("Основное", {"fields": ("name", "menu_name", "slug", "parent", "description", "icon", "full_path_link")}),
        ("Показ", {"fields": ("is_active", "show_in_menu", "order")}),
        ("SEO", {"classes": ("collapse",), "fields": ("seo_title", "seo_description")}),
        ("Курсы в подборке", {"fields": ("courses_info",)}),
    )

    class Media:
        css = {"all": ("admin/podborki/podborki-admin.css",)}
        js = ("admin/podborki/podborki-admin.js",)

    # ---------- данные для списка ----------
    def changelist_view(self, request, extra_context=None):
        self._counts = admin_counts()
        self._parents = set(CourseTag.objects.exclude(parent__isnull=True).values_list("parent_id", flat=True))
        extra_context = extra_context or {}
        extra_context["reorder_url"] = tag_url("reorder")
        return super().changelist_view(request, extra_context)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("parent")

    def get_ordering(self, request):
        """Порядок дерева (родитель → дети по order) — через CASE по id, работает с пагинацией и фильтрами."""
        ids = [t.pk for t in tree_ordered()]
        if not ids:
            return ["full_path"]
        return [Case(*[When(pk=pk, then=Value(i)) for i, pk in enumerate(ids)], default=Value(len(ids)), output_field=IntegerField())]

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    # ---------- колонки ----------
    @admin.display(description="")
    def drag(self, obj):
        return format_html('<span class="pdb-drag" draggable="true" title="Перетащите, чтобы изменить порядок" data-id="{}" data-parent="{}" data-level="{}">⋮⋮</span>', obj.pk, obj.parent_id or "", obj.level)

    @admin.display(description="Подборка", ordering="full_path")
    def tree_name(self, obj):
        return format_html(
            '<div class="pdb-name" style="--lvl:{}"><a href="{}">{}</a> <span class="pdb-level">ур. {}</span></div><div class="pdb-path" style="--lvl:{}">в меню: «{}» · /podborki/{}/</div>',
            obj.level, tag_url("change", obj.pk), obj.name, obj.level + 1, obj.level, obj.display_name, obj.full_path,
        )

    @admin.display(description="В меню как")
    def menu_name_col(self, obj):
        return obj.menu_name or "—"

    @admin.display(description="Курсов")
    def direct_col(self, obj):
        n = self._counts.get(obj.pk, (0, 0))[0]
        if not n:
            return format_html('<span class="pdb-muted">0</span>')
        return format_html('<a href="{}">{}</a>', course_list_url(obj.pk), n)

    @admin.display(description="Всего")
    def total_col(self, obj):
        return format_html("<strong>{}</strong>", self._counts.get(obj.pk, (0, 0))[1])

    @admin.display(description="Порядок")
    def order_col(self, obj):
        return format_html('<button type="button" class="pdb-move" data-dir="-1" data-id="{0}" title="Выше">↑</button><button type="button" class="pdb-move" data-dir="1" data-id="{0}" title="Ниже">↓</button>', obj.pk)

    @admin.display(description="Действия")
    def actions_col(self, obj):
        edit = format_html('<a class="pdb-act" href="{}" title="Изменить">✎</a>', tag_url("change", obj.pk))
        if obj.level < MAX_DEPTH - 1:
            add = format_html('<a class="pdb-act" href="{}?parent={}" title="Добавить вложенную">＋</a>', tag_url("add"), obj.pk)
        else:
            add = format_html('<span class="pdb-act pdb-act--off" title="Максимум {} уровня">＋</span>', MAX_DEPTH)
        direct, _ = self._counts.get(obj.pk, (0, 0))
        has_children = obj.pk in self._parents
        if direct == 0 and not has_children:
            delete = format_html('<a class="pdb-act pdb-act--del" href="{}" title="Удалить">🗑</a>', tag_url("delete", obj.pk))
        else:
            reasons = []
            if has_children:
                reasons.append("есть вложенные подборки")
            if direct:
                reasons.append(f"привязано курсов: {direct}")
            delete = format_html('<span class="pdb-act pdb-act--lock" tabindex="0" title="Нельзя удалить: {}">🔒</span>', "; ".join(reasons))
        return format_html("{}{}{}", edit, add, delete)

    # ---------- форма ----------
    @admin.display(description="Адрес на сайте")
    def full_path_link(self, obj):
        if not obj.pk:
            return "Появится после сохранения"
        return format_html('<a href="{0}" target="_blank">{0}</a>', obj.get_absolute_url())

    @admin.display(description="Курсы")
    def courses_info(self, obj):
        if not obj.pk:
            return "Курсы добавляются в карточке курса, поле «Подборки»."
        direct, total = admin_counts().get(obj.pk, (0, 0))
        return format_html(
            'Привязано напрямую: <strong>{}</strong> · вместе с вложенными: <strong>{}</strong>. '
            'Курсы добавляются в карточке курса, поле «Подборки». <a href="{}">Открыть список курсов →</a>',
            direct, total, course_list_url(obj.pk),
        )

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        if request.GET.get("parent"):
            initial["parent"] = request.GET["parent"]
        return initial

    # ---------- удаление ----------
    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)
        if obj is not None:
            reasons = obj.delete_blockers()
            if reasons:
                courses = obj.courses.all()[:5]
                return render(request, "admin/podborki/coursetag/delete_blocked.html", {
                    **self.admin_site.each_context(request),
                    "opts": self.model._meta, "object": obj, "reasons": reasons,
                    "courses": courses, "courses_total": obj.courses.count(),
                    "children": obj.children.all(),
                    "courses_url": course_list_url(obj.pk),
                    "title": "Удалить нельзя",
                })
        return super().delete_view(request, object_id, extra_context)

    def delete_model(self, request, obj):
        try:
            obj.delete()
        except (ValidationError, ProtectedError) as e:
            self.message_user(request, str(getattr(e, "message", e.args[0])), messages.ERROR)

    @admin.action(description="Удалить выбранные (только без курсов и вложенных)", permissions=["delete"])
    def safe_delete(self, request, queryset):
        deleted, skipped = [], []
        for tag in sorted(queryset, key=lambda t: -t.level):
            if tag.can_delete():
                name = tag.name
                tag.delete()
                deleted.append(name)
            else:
                skipped.append(f"«{tag.name}»")
        if deleted:
            self.message_user(request, f"Удалено подборок: {len(deleted)}.", messages.SUCCESS)
        if skipped:
            self.message_user(request, "Пропущено — привязаны курсы или есть вложенные: " + ", ".join(skipped), messages.WARNING)

    @admin.action(description="Сделать активными")
    def make_active(self, request, queryset):
        queryset.update(is_active=True)
        invalidate_menu_cache()

    @admin.action(description="Скрыть")
    def make_hidden(self, request, queryset):
        queryset.update(is_active=False)
        invalidate_menu_cache()

    @admin.action(description="Показывать в меню")
    def add_to_menu(self, request, queryset):
        queryset.update(show_in_menu=True)
        invalidate_menu_cache()

    @admin.action(description="Убрать из меню")
    def remove_from_menu(self, request, queryset):
        queryset.update(show_in_menu=False)
        invalidate_menu_cache()

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        invalidate_menu_cache()

    # ---------- сортировка ----------
    def get_urls(self):
        o = self.model._meta
        return [path("reorder/", self.admin_site.admin_view(self.reorder_view), name=f"{o.app_label}_{o.model_name}_reorder")] + super().get_urls()

    def reorder_view(self, request):
        """POST JSON {"parent": id|null, "ids": [id, id, ...]} — новый порядок детей одного родителя."""
        if request.method != "POST":
            return JsonResponse({"error": "POST only"}, status=405)
        if not self.has_change_permission(request):
            raise PermissionDenied
        data = json.loads(request.body or "{}")
        parent = data.get("parent") or None
        ids = [int(i) for i in data.get("ids", [])]
        siblings = set(CourseTag.objects.filter(parent_id=parent).values_list("id", flat=True))
        if set(ids) != siblings:
            return JsonResponse({"error": "Можно менять порядок только внутри одного уровня"}, status=400)
        with transaction.atomic():
            for i, pk in enumerate(ids):
                CourseTag.objects.filter(pk=pk).update(order=(i + 1) * 10)
        invalidate_menu_cache()
        return JsonResponse({"ok": True})


# ---------- для CourseAdmin ----------
class TagTreeFilter(admin.SimpleListFilter):
    """Фильтр списка курсов по подборке — вместе с вложенными."""

    title = "подборка"
    parameter_name = "podborka"

    def lookups(self, request, model_admin):
        return [(str(t.pk), ("— " * t.level) + t.name) for t in tree_ordered()] + [("none", "Без подборок")]

    def queryset(self, request, qs):
        if self.value() == "none":
            return qs.filter(tags__isnull=True)
        if self.value():
            tag = CourseTag.objects.filter(pk=self.value()).first()
            if tag:
                return qs.filter(tags__in=tag.descendant_ids()).distinct()
        return qs


class TagAssignForm(ActionForm):
    tag = forms.ChoiceField(required=False, label="Подборка", choices=())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tag"].choices = [("", "— подборка —")] + [(t.pk, ("— " * t.level) + t.name) for t in tree_ordered()]


class CourseTagsAdminMixin:
    """
    Добавьте в свой CourseAdmin:  class CourseAdmin(CourseTagsAdminMixin, admin.ModelAdmin): ...
    и "tags" в fields/fieldsets, TagTreeFilter в list_filter, "tags_col" в list_display.
    """

    action_form = TagAssignForm
    tag_actions = ["add_to_tag", "remove_from_tag"]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "tags":
            kwargs["widget"] = TagTreeWidget()
            kwargs["queryset"] = CourseTag.objects.all()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("tags")

    @admin.display(description="Подборки")
    def tags_col(self, obj):
        tags = list(obj.tags.all())
        if not tags:
            return format_html('<span style="color:#999">—</span>')
        return format_html_join("", '<span class="pdb-tag">{}</span>', ((t.display_name,) for t in tags))

    def get_actions(self, request):
        actions = super().get_actions(request)
        for name in self.tag_actions:
            func = getattr(self, name)
            actions[name] = (func, name, func.short_description)
        return actions

    def add_to_tag(self, modeladmin, request, queryset):
        tag = CourseTag.objects.filter(pk=request.POST.get("tag")).first()
        if not tag:
            self.message_user(request, "Выберите подборку в поле рядом с действием.", messages.WARNING)
            return
        for c in queryset:
            c.tags.add(tag)
        invalidate_menu_cache()
        self.message_user(request, f"Добавлено в «{tag}»: {queryset.count()}.", messages.SUCCESS)

    add_to_tag.short_description = "Добавить в подборку…"

    def remove_from_tag(self, modeladmin, request, queryset):
        tag = CourseTag.objects.filter(pk=request.POST.get("tag")).first()
        if not tag:
            self.message_user(request, "Выберите подборку в поле рядом с действием.", messages.WARNING)
            return
        for c in queryset:
            c.tags.remove(tag)
        invalidate_menu_cache()
        self.message_user(request, f"Убрано из «{tag}»: {queryset.count()}.", messages.SUCCESS)

    remove_from_tag.short_description = "Убрать из подборки…"
