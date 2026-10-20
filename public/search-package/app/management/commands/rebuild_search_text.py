from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Заполняет поле search_text у курсов и профессий (после добавления SearchTextMixin или массового импорта)."

    def add_arguments(self, parser):
        parser.add_argument("--models", default="", help="app_label.Model через запятую; по умолчанию все модели с search_text")

    def handle(self, *args, **opts):
        if opts["models"]:
            models = [apps.get_model(m.strip()) for m in opts["models"].split(",") if m.strip()]
        else:
            models = [m for m in apps.get_models() if any(f.name == "search_text" for f in m._meta.fields)]
        for model in models:
            batch, total = [], 0
            for obj in model.objects.all().iterator(chunk_size=500):
                obj.search_text = obj.build_search_text()
                batch.append(obj)
                if len(batch) >= 500:
                    model.objects.bulk_update(batch, ["search_text"])
                    total += len(batch)
                    batch = []
            if batch:
                model.objects.bulk_update(batch, ["search_text"])
                total += len(batch)
            self.stdout.write(self.style.SUCCESS(f"{model.__name__}: {total}"))
