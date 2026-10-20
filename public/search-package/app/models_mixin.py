"""
Нужен, если база — SQLite (или для ускорения на большой базе PostgreSQL).
Добавьте миксин к моделям Course и Profession, сделайте makemigrations/migrate
и заполните поле: python manage.py rebuild_search_text
"""
from django.db import models


def make_search_text(*parts):
    from .search_utils import normalize

    return normalize(" ".join(p for p in parts if p))


class SearchTextMixin(models.Model):
    search_text = models.CharField(max_length=400, blank=True, default="", db_index=True, editable=False)

    class Meta:
        abstract = True

    def build_search_text(self):
        return make_search_text(getattr(self, "name", ""))

    def save(self, *args, **kwargs):
        self.search_text = self.build_search_text()
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and "search_text" not in update_fields:
            kwargs["update_fields"] = list(update_fields) + ["search_text"]
        super().save(*args, **kwargs)
