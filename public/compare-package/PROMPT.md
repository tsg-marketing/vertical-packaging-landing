# Промпт для Cline: сравнение курсов без ограничений

Перед запуском:
1. Сделайте коммит в git.
2. Распакуйте архив и положите папку `compare-package/` в корень Django-проекта как `_design/compare-package/`.
3. Откройте в браузере `_design/compare-package/mockups/compare/index.html` — так должна выглядеть таблица.

Запускайте в режиме **Plan**, проверьте план, затем **Act**.

```
Внедри сравнение курсов без ограничения по количеству. Готовые файлы — в _design/compare-package/ (прочитай README.md). Используй их, не пиши с нуля. Эталон вида: _design/compare-package/mockups/ (поиск по "COMPARE:" и классам cmp-).

ВАЖНО: на сайте уже может быть сравнение с лимитом 4 курса (старый compare.js с MAX = 4, MAX_COMPARE в context_processors.py, "до 4" в шаблонах). Найди всё это (grep -rn "MAX_COMPARE\|var MAX\|до 4\|из 4\|repeat(4" .) и замени на новые файлы. Старые файлы удали, только если они полностью заменены.

1. Изучи проект: где модели Course и School, есть ли slug у обоих, FK course.school, имя URL страницы сравнения и каталога в urls.py, есть ли base.html с блоками title/robots/content, как подключается статика. Покажи кратко.

2. Статика:
   - static/edukursy/js/compare.js → в статику (заменить старый, если есть).
   - Стили: если на сайте подключён полный style.css из основного пакета edukursy — найди в нём блок «КНОПКА «СРАВНИТЬ»» и раздел «СРАВНЕНИЕ КУРСОВ /compare/» и замени их на содержимое compare.css (без :root в начале). Если CSS у сайта свой — подключи compare.css отдельным <link> в base.html и переменные из :root сверь с цветами сайта.

3. Python (в приложение каталога, назову его <app>):
   - app/compare_utils.py → <app>/compare_utils.py
   - app/context_processors.py → <app>/context_processors.py, добавь "<app>.context_processors.compare" в settings.TEMPLATES[0]["OPTIONS"]["context_processors"]
   - app/templatetags/compare_tags.py → <app>/templatetags/ (создай __init__.py, если нет)
   - app/views_compare.py → логику перенеси в существующий view сравнения или подключи как новый. URL: path("compare/", compare_view, name="compare") — имя "compare" используется в шаблонах; если у меня другое имя — поправь шаблоны.
   - Проверь ROW_SPECS во views_compare.py: имена полей (duration_months, price_month, projects_count, mentor, homework_review, free_lesson, final_project, tax_deduction, certificate, refund, rating) сверь с моими моделями и поправь лямбды. Поля, которых нет, НЕ добавляй в модели — getattr(..., None) вернёт None, и строка сама не выведется.
   - Если у Course нет get_absolute_url — добавь.
   - app/tests/test_compare_utils.py → <app>/tests/ и запусти: python manage.py test <app>.tests.test_compare_utils

4. Шаблоны:
   - templates/edukursy/partials/compare/*.html → в мои шаблоны.
   - templates/edukursy/compare/compare.html → страница /compare/. Если base.html у меня с другими блоками: body_attrs (атрибуты <body>), robots, after_main (после </main>, для липкой мобильной панели) — добавь эти блоки в base.html, ничего в нём не ломая.
   - base.html: <body{% block body_attrs %} data-compare-url="{% url 'compare' %}"{% endblock %}> и перед </body> после основного script.js: {% include "edukursy/partials/compare/scripts.html" %}.
   - Если в шаблоне используются partials/breadcrumbs.html и partials/ad_slot.html, а у меня их нет — замени на мою разметку крошек или убери.

5. Кнопка «Сравнить»:
   - Во ВСЕХ карточках курса (каталог, страница профессии, страница школы, «Похожие курсы», главная) — первым ребёнком <article class="catalog-card">, ДО ссылки <a class="catalog-card__link"> (не внутри <a>):
     {% include "edukursy/partials/compare/button.html" with course=course variant="card" %}
   - Страница курса, карточка цены, после «Бесплатного вводного урока»:
     {% include "edukursy/partials/compare/button.html" with course=course variant="block" label_off="Добавить к сравнению" label_on="Добавлен к сравнению" %}
     {% include "edukursy/partials/compare/link.html" %}
   - Липкая мобильная панель .sticky-cta: оберни «На сайт школы» в <div class="sticky-cta__actions"> и поставь перед ней variant="icon".
   - Если в шапке курса уже есть старая кнопка «Сравнить курс» — удали её (кнопка в карточке цены её заменяет), иначе будет две кнопки.

6. Проверь руками (и покажи мне результат):
   - добавь 7+ курсов из каталога: все добавляются, сообщения о лимите НЕТ; в панели снизу курсы в одну строку, справа стрелка прокрутки; кнопка «Сравнить 7 курсов»;
   - счётчик в меню «Сравнения» = 7;
   - /compare/: 7 колонок, таблица прокручивается вбок, колонка «Параметр» закреплена, над таблицей «1–4 из 7» и стрелки; «Лучшее» подсвечено по всем 7 курсам;
   - × у колонки убирает курс, URL обновляется; убери все — пустое состояние «Добавьте курсы для сравнения»;
   - «Только различия» скрывает строки с одинаковыми значениями;
   - перезагрузка каталога — кнопки сразу нажаты (без мигания);
   - ширина 390 px: панель сворачивается по тапу, не перекрывает «На сайт школы»; липкая панель на /compare/ прокручивается вбок;
   - на /compare/ число SQL-запросов не зависит от числа курсов (один запрос на курсы + один на список «Добавить»).

Покажи diff шаблонов и base.html перед сохранением.
```

## Если что-то пошло не так

- **Кнопка внутри ссылки, клик уводит на курс** → «Перенеси include кнопки из <a class="catalog-card__link"> на уровень выше, первым ребёнком <article>.»
- **Кнопки мигают при загрузке** → «Проверь, что context processor compare подключён в settings и compare_ids есть в контексте шаблона карточки.»
- **Таблица не прокручивается / колонки сжаты** → «Сверь классы таблицы с _design/compare-package/mockups/compare/index.html: обёртка .cmp-table-wrap > .cmp-scroll[data-cmp-scroll] > table.cmp-table, у th колонок класс cmp-col. CSS не меняй.»
- **Курс добавлен, но на /compare/ его нет** → «Проверь формат id: должно быть "<school.slug>/<course.slug>" и в фильтре compare_id, и в resolve_courses.»
