"""
Админка курса: поля extract_json и editorial_json.

- Большие моноширинные поля с кнопками «Форматировать», «Очистить», «Вставить пустой шаблон» и счётчиком.
- Принимает JSON как есть или в обёртке ```json ... ``` (как отдаёт нейросеть).
- Проверка при сохранении: синтаксис (с номером строки) и типы по схеме — ошибки не дают сохранить,
  предупреждения (лишние/отсутствующие ключи) показываются сообщением.
- Блок «Что выведется на странице»: какие блоки будут показаны, какие пропущены и из какого ключа взяты.
- Колонка «Разбор» в списке курсов и фильтр «Разбор: есть/нет/частично/ошибка».

Подключение — в CourseAdmin:
    class CourseAdmin(CourseJsonAdminMixin, ...):  (миксин — первым)
        fieldsets = (..., CourseJsonAdminMixin.json_fieldset, ...)
        list_display = (..., "json_status_col")
        list_filter = (..., JsonStatusFilter)
"""
import json

from django import forms
from django.contrib import admin, messages
from django.db.models import Q
from django.utils.html import format_html, format_html_join

from .course_json import (
    EDITORIAL_KEYS, EXTRACT_KEYS, SOURCE_FACT_KEYS, build_course_page, parse_json,
    validate_editorial, validate_extract,
)


def empty_template(schema):
    out = {}
    for key, kind in schema.items():
        if kind.startswith("list") or kind == "faq":
            out[key] = []
        elif kind == "facts":
            out[key] = {k: None for k in SOURCE_FACT_KEYS}
        else:
            out[key] = None
    return out


class JsonTextarea(forms.Textarea):
    template_name = "course_page/admin/json_textarea.html"

    def __init__(self, kind, attrs=None):
        self.kind = kind
        super().__init__(attrs={"rows": 18, "class": "cp-json", "spellcheck": "false", **(attrs or {})})

    def format_value(self, value):
        if value in (None, "", {}, []):
            return ""
        if isinstance(value, str):
            try:
                value = parse_json(value)
            except (ValueError, TypeError):
                return value
        return json.dumps(value, ensure_ascii=False, indent=2)

    def get_context(self, name, value, attrs):
        ctx = super().get_context(name, value, attrs)
        schema = EXTRACT_KEYS if self.kind == "extract" else EDITORIAL_KEYS
        ctx["widget"]["kind"] = self.kind
        ctx["widget"]["template_json"] = json.dumps(empty_template(schema), ensure_ascii=False, indent=2)
        return ctx

    def render(self, name, value, attrs=None, renderer=None):
        from django.template.loader import render_to_string
        from django.utils.safestring import mark_safe

        return mark_safe(render_to_string(self.template_name, self.get_context(name, value, attrs)))

    class Media:
        css = {"all": ("admin/course_page/course-json-admin.css",)}
        js = ("admin/course_page/course-json-admin.js",)


class JsonDictField(forms.CharField):
    """Текст → dict. Пусто → {} (или None для nullable-поля)."""

    def __init__(self, kind, nullable=False, **kwargs):
        self.kind = kind
        self.nullable = nullable
        kwargs.setdefault("required", False)
        kwargs["widget"] = JsonTextarea(kind)
        kwargs.pop("encoder", None)
        kwargs.pop("decoder", None)
        kwargs.pop("max_length", None)
        super().__init__(**kwargs)

    def prepare_value(self, value):
        return value

    def to_python(self, value):
        if value in (None, ""):
            return None if self.nullable else {}
        if isinstance(value, dict):
            return value
        try:
            return parse_json(value)
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f"Ошибка в JSON: строка {e.lineno}, позиция {e.colno} — {e.msg}. Проверьте запятые и кавычки.")
        except ValueError as e:
            raise forms.ValidationError(str(e))

    def validate(self, value):
        super().validate(value)
        if not value:
            return
        errors, _ = (validate_extract if self.kind == "extract" else validate_editorial)(value)
        if errors:
            raise forms.ValidationError(["Неверный формат:"] + errors)

    def has_changed(self, initial, data):
        try:
            return (parse_json(initial) or {}) != (self.to_python(data) or {})
        except forms.ValidationError:
            return True


class JsonStatusFilter(admin.SimpleListFilter):
    title = "разбор (JSON)"
    parameter_name = "json"

    def lookups(self, request, model_admin):
        return [("both", "Оба JSON"), ("extract", "Только extract"), ("editorial", "Только editorial"), ("none", "Нет разбора"), ("failed", "Статус failed")]

    def queryset(self, request, qs):
        has_ex = Q(extract_json__has_key="extraction_status") | Q(extract_json__has_key="course_title")
        has_ed = Q(editorial_json__has_key="draft_status") | Q(editorial_json__has_key="editorial_intro")
        v = self.value()
        if v == "both":
            return qs.filter(has_ex & has_ed)
        if v == "extract":
            return qs.filter(has_ex).exclude(has_ed)
        if v == "editorial":
            return qs.filter(has_ed).exclude(has_ex)
        if v == "none":
            return qs.exclude(has_ex).exclude(has_ed)
        if v == "failed":
            return qs.filter(Q(extract_json__extraction_status="failed") | Q(editorial_json__draft_status="failed"))
        return qs


class CourseJsonAdminMixin:
    json_fieldset = (
        "Разбор курса (JSON)",
        {
            "fields": ("extract_json", "editorial_json", "json_blocks_report"),
            "description": "Вставьте ответ нейросети целиком — можно вместе с ```json. Блок на странице выводится, только если в JSON есть данные по ключу.",
        },
    )

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if "json_blocks_report" not in ro:
            ro.append("json_blocks_report")
        return ro

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in ("extract_json", "editorial_json"):
            kind = "extract" if db_field.name == "extract_json" else "editorial"
            label = "Факты со страницы школы (extract_json)" if kind == "extract" else "Текст редакции (editorial_json)"
            return JsonDictField(kind, nullable=db_field.null, label=label, help_text=db_field.help_text)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        for name, check in (("extract_json", validate_extract), ("editorial_json", validate_editorial)):
            data = form.cleaned_data.get(name)
            if not data:
                continue
            _, warnings = check(data)
            for w in warnings[:5]:
                self.message_user(request, f"{name}: {w}", messages.WARNING)
            status = data.get("extraction_status") or data.get("draft_status")
            if status == "failed":
                self.message_user(request, f"{name}: статус failed — этот JSON на странице не выводится.", messages.WARNING)

    @admin.display(description="Что выведется на странице")
    def json_blocks_report(self, obj):
        if not obj or not obj.pk:
            return "Появится после сохранения."
        page = build_course_page(obj)
        rows = page.report()
        shown = sum(1 for _, ok, _ in rows if ok)
        status = []
        if page.extract_status:
            status.append(f"extract: {page.extract_status}")
        if page.editorial_status:
            status.append(f"editorial: {page.editorial_status}")
        items = format_html_join(
            "",
            '<li class="cp-rep__row cp-rep__row--{}"><span class="cp-rep__mark">{}</span><span class="cp-rep__name">{}</span><code class="cp-rep__src">{}</code></li>',
            (("on" if ok else "off", "✓" if ok else "—", name, src) for name, ok, src in rows),
        )
        link = ""
        if hasattr(obj, "get_absolute_url"):
            link = format_html(' · <a href="{}" target="_blank">Открыть страницу ↗</a>', obj.get_absolute_url())
        return format_html(
            '<div class="cp-rep"><p class="cp-rep__head"><strong>Блоков на странице: {} из {}</strong>{}{}</p><ul class="cp-rep__list">{}</ul></div>',
            shown, len(rows), format_html(" · {}", ", ".join(status)) if status else "", link, items,
        )

    @admin.display(description="Разбор")
    def json_status_col(self, obj):
        ex = obj.extract_json if isinstance(obj.extract_json, dict) else {}
        ed = obj.editorial_json if isinstance(obj.editorial_json, dict) else {}
        def badge(label, data, key):
            if not data:
                return format_html('<span class="cp-badge cp-badge--none" title="Нет данных">{} —</span>', label)
            st = data.get(key) or "?"
            return format_html('<span class="cp-badge cp-badge--{}" title="{}: {}">{} {}</span>', st, key, st, label, {"ok": "✓", "partial": "½", "failed": "✕"}.get(st, "?"))
        return format_html("{} {}", badge("E", ex, "extraction_status"), badge("R", ed, "draft_status"))

    class Media:
        css = {"all": ("admin/course_page/course-json-admin.css",)}
