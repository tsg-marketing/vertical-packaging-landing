from django.core.management.base import BaseCommand

from ...models import CourseTag

TREE = [
    ("Курсы с трудоустройством", "С трудоустройством", "s-trudoustrojstvom", "briefcase", [
        ("Курсы с трудоустройством сразу", "Трудоустройство сразу", "srazu", "", [
            ("Курсы с трудоустройством сразу в IT", "В IT", "v-it", "", []),
            ("Курсы с трудоустройством сразу не в IT", "Не в IT", "ne-v-it", "", []),
        ]),
        ("Курсы с трудоустройством после стажировки", "После стажировки", "posle-stazhirovki", "", [
            ("Курсы со стажировкой в IT", "В IT", "v-it", "", []),
            ("Курсы со стажировкой не в IT", "Не в IT", "ne-v-it", "", []),
        ]),
        ("Курсы с гарантией трудоустройства", "С гарантией в договоре", "s-garantiej", "", []),
    ]),
    ("Курсы для начинающих", "Для начинающих", "dlya-nachinayushchih", "sprout", [
        ("Курсы в IT без опыта", "IT без опыта", "it-bez-opyta", "", []),
        ("Курсы для гуманитариев", "Для гуманитариев", "dlya-gumanitariev", "", []),
        ("Курсы для смены профессии после 40", "После 40 лет", "posle-40", "", []),
    ]),
    ("Курсы для детей", "Для детей", "dlya-detej", "smile", [
        ("Курсы для детей 7–10 лет", "7–10 лет", "7-10-let", "", [
            ("Программирование для детей 7–10 лет", "Программирование", "programmirovanie", "", []),
            ("Рисование и дизайн для детей 7–10 лет", "Рисование и дизайн", "risovanie", "", []),
        ]),
        ("Курсы для детей 11–14 лет", "11–14 лет", "11-14-let", "", [
            ("Программирование для детей 11–14 лет", "Программирование", "programmirovanie", "", []),
            ("Разработка игр для детей 11–14 лет", "Разработка игр", "razrabotka-igr", "", []),
        ]),
        ("Подготовка к ЕГЭ и ОГЭ", "ЕГЭ и ОГЭ", "ege-oge", "", []),
    ]),
    ("Бесплатные курсы", "Бесплатные", "besplatnye", "gift", []),
    ("Курсы в рассрочку", "В рассрочку", "v-rassrochku", "wallet", []),
    ("Короткие курсы до 3 месяцев", "Короткие, до 3 месяцев", "korotkie", "timer", []),
]


class Command(BaseCommand):
    help = "Создаёт пример дерева подборок (существующие с тем же путём не трогает)."

    def handle(self, *args, **opts):
        created = 0

        def walk(items, parent=None):
            nonlocal created
            for i, (name, menu, slug, icon, kids) in enumerate(items):
                tag, is_new = CourseTag.objects.get_or_create(
                    parent=parent, slug=slug,
                    defaults={"name": name, "menu_name": menu, "icon": icon, "order": (i + 1) * 10},
                )
                created += is_new
                walk(kids, tag)

        walk(TREE)
        self.stdout.write(self.style.SUCCESS(f"Создано подборок: {created}"))
