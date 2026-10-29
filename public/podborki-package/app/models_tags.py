"""
Подборки курсов (CourseTag) — иерархия до 3 уровней.

Подключение:
  1) скопируйте класс CourseTag в models.py приложения каталога (или импортируйте отсюда);
  2) в модель Course добавьте:
         tags = models.ManyToManyField("CourseTag", blank=True, related_name="courses", verbose_name="Подборки")
  3) makemigrations + migrate.

Без сторонних библиотек (django-mptt не нужен): при 3 уровнях и сотнях подборок
дерево целиком строится одним запросом и кэшируется.
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.text import slugify

MAX_DEPTH = 3

ICON_CHOICES = [
    ("", "— без иконки —"),
    ("briefcase", "Портфель (трудоустройство)"),
    ("sprout", "Росток (для начинающих)"),
    ("smile", "Смайл (для детей)"),
    ("gift", "Подарок (бесплатные)"),
    ("wallet", "Кошелёк (рассрочка)"),
    ("timer", "Таймер (короткие)"),
    ("star", "Звезда"),
    ("graduation-cap", "Шапочка выпускника"),
]


class CourseTagQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def roots(self):
        return self.filter(parent__isnull=True)


class CourseTag(models.Model):
    name = models.CharField("Название", max_length=150, help_text="Заголовок страницы подборки (H1).")
    menu_name = models.CharField("Название в меню", max_length=60, blank=True, help_text="Короткий вариант для меню. Если пусто — берётся «Название».")
    slug = models.SlugField("Slug", max_length=80, allow_unicode=False, help_text="Часть адреса. Уникален внутри родителя.")
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children",
        verbose_name="Родительская подборка", help_text="Пусто — 1-й уровень. Глубже 3 уровней вложить нельзя.",
    )
    description = models.TextField("Описание", blank=True, help_text="Текст под заголовком на странице подборки.")
    icon = models.CharField("Иконка", max_length=30, blank=True, choices=ICON_CHOICES, help_text="Только для 1-го уровня — показывается в меню.")
    is_active = models.BooleanField("Активна", default=True, db_index=True, help_text="Скрытая подборка не видна на сайте, её страница отдаёт 404.")
    show_in_menu = models.BooleanField("Показывать в меню", default=True, help_text="Можно убрать из меню, но оставить страницу.")
    order = models.PositiveIntegerField("Порядок", default=0, db_index=True, help_text="Меньше — выше. Удобнее менять перетаскиванием в списке.")
    seo_title = models.CharField("SEO title", max_length=200, blank=True)
    seo_description = models.CharField("Meta description", max_length=300, blank=True)

    level = models.PositiveSmallIntegerField("Уровень", default=0, editable=False)
    full_path = models.CharField("Путь", max_length=255, editable=False, db_index=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CourseTagQuerySet.as_manager()

    class Meta:
        verbose_name = "подборка курсов"
        verbose_name_plural = "подборки курсов"
        ordering = ["full_path"]
        constraints = [
            models.UniqueConstraint(fields=["parent", "slug"], name="coursetag_unique_slug_in_parent"),
            models.UniqueConstraint(fields=["slug"], condition=Q(parent__isnull=True), name="coursetag_unique_root_slug"),
        ]

    def __str__(self):
        return self.name

    @property
    def path_name(self):
        """«С трудоустройством › Сразу › В IT» (делает запросы к родителям — не использовать в циклах)."""
        return " › ".join(t.display_name for t in self.ancestors(include_self=True))

    @property
    def display_name(self):
        return self.menu_name or self.name

    def get_absolute_url(self):
        return reverse("podborka", kwargs={"path": self.full_path})

    # ---------- дерево ----------
    def ancestors(self, include_self=False):
        chain, node, seen = [], self if include_self else self.parent, set()
        while node is not None and node.pk not in seen:
            seen.add(node.pk)
            chain.insert(0, node)
            node = node.parent
        return chain

    def descendant_ids(self, include_self=True):
        """Все id вложенных подборок одним запросом по full_path."""
        ids = list(CourseTag.objects.filter(full_path__startswith=self.full_path + "/").values_list("id", flat=True))
        return ([self.pk] if include_self else []) + ids

    def subtree_height(self):
        """Сколько уровней под подборкой (0 — нет детей)."""
        paths = CourseTag.objects.filter(full_path__startswith=self.full_path + "/").values_list("full_path", flat=True)
        base = self.full_path.count("/")
        return max((p.count("/") - base for p in paths), default=0)

    # ---------- валидация ----------
    def clean(self):
        if self.slug:
            self.slug = self.slug.strip().lower()
        if not self.slug and self.name:
            self.slug = slugify(self.name, allow_unicode=False)[:80]
        if self.parent_id:
            if self.pk and self.parent_id == self.pk:
                raise ValidationError({"parent": "Нельзя выбрать родителем саму подборку."})
            parent = self.parent
            if self.pk:
                for a in parent.ancestors(include_self=True):
                    if a.pk == self.pk:
                        raise ValidationError({"parent": "Нельзя выбрать родителем вложенную подборку."})
            new_level = parent.level + 1
        else:
            new_level = 0
        height = self.subtree_height() if self.pk else 0
        if new_level + height + 1 > MAX_DEPTH:
            raise ValidationError({"parent": f"Нельзя вложить глубже {MAX_DEPTH} уровней: у подборки есть вложенные, вместе получится {new_level + height + 1}."})
        qs = CourseTag.objects.filter(parent_id=self.parent_id, slug=self.slug)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if self.slug and qs.exists():
            raise ValidationError({"slug": f"Подборка с адресом «{self.slug}» уже есть у этого родителя."})

    # ---------- сохранение ----------
    def _compute_path(self):
        self.level = self.parent.level + 1 if self.parent_id else 0
        self.full_path = f"{self.parent.full_path}/{self.slug}" if self.parent_id else self.slug

    def save(self, *args, **kwargs):
        old_path = None
        if self.pk:
            old_path = CourseTag.objects.filter(pk=self.pk).values_list("full_path", flat=True).first()
        if not self.slug:
            self.slug = slugify(self.name)[:80] or "podborka"
        self._compute_path()
        super().save(*args, **kwargs)
        if old_path and old_path != self.full_path:
            for child in CourseTag.objects.filter(full_path__startswith=old_path + "/").order_by("level"):
                child.parent = CourseTag.objects.get(pk=child.parent_id)
                child._compute_path()
                CourseTag.objects.filter(pk=child.pk).update(level=child.level, full_path=child.full_path)
        from .podborki_services import invalidate_menu_cache

        invalidate_menu_cache()

    # ---------- удаление ----------
    def delete_blockers(self):
        """Причины, по которым удалить нельзя. Пустой список — можно удалять."""
        reasons = []
        n_children = self.children.count()
        if n_children:
            names = ", ".join(f"«{c.display_name}»" for c in self.children.all()[:3])
            reasons.append(f"есть вложенные подборки ({n_children}): {names}")
        n_courses = self.courses.count()
        if n_courses:
            reasons.append(f"к подборке привязано курсов: {n_courses}")
        return reasons

    def can_delete(self):
        return not self.delete_blockers()

    def delete(self, *args, **kwargs):
        reasons = self.delete_blockers()
        if reasons:
            raise ValidationError(f"Подборку «{self.name}» нельзя удалить: " + "; ".join(reasons) + ".")
        result = super().delete(*args, **kwargs)
        from .podborki_services import invalidate_menu_cache

        invalidate_menu_cache()
        return result


# ---------- защита от удаления любым способом (QuerySet.delete, каскад из админки, shell) ----------
from django.db.models import ProtectedError  # noqa: E402
from django.db.models.signals import pre_delete  # noqa: E402
from django.dispatch import receiver  # noqa: E402


@receiver(pre_delete, sender=CourseTag)
def protect_used_tag(sender, instance, **kwargs):
    reasons = instance.delete_blockers()
    if reasons:
        raise ProtectedError(f"Подборку «{instance.name}» нельзя удалить: " + "; ".join(reasons) + ".", set())


def connect_course_tags_signal():
    """Сбрасывает кэш меню при изменении Course.tags откуда угодно. Вызывается из AppConfig.ready() или в конце models.py."""
    from django.db.models.signals import m2m_changed

    from .podborki_services import invalidate_menu_cache

    through = CourseTag._meta.get_field("courses").through

    def _changed(sender, action, **kwargs):
        if action in ("post_add", "post_remove", "post_clear"):
            invalidate_menu_cache()

    m2m_changed.connect(_changed, sender=through, weak=False, dispatch_uid="podborki_tags_changed")
