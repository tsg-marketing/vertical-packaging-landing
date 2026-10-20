# Промпт для Cline: строка поиска с подсказками

Перед запуском:
1. Сделайте коммит в git.
2. Распакуйте архив, папку `search-package/` положите в корень Django-проекта как `_design/search-package/`.
3. Откройте `_design/search-package/mockups/index.html` в браузере и наберите в поиске «pyt», «диз», «ghjuh» — так должно работать на сайте.

Запускайте в режиме **Plan**, проверьте план, затем **Act**.

```
Добавь на сайт строку поиска под главным меню с подсказками при вводе. Поиск — по названию курса и профессии из базы. Готовые файлы — в _design/search-package/ (прочитай README.md). Используй их, не пиши с нуля. Эталон вида и поведения: _design/search-package/mockups/index.html (поиск по "SEARCH:").

1. Изучи проект и покажи кратко:
   - модели Course, Profession, School: поля name, slug, FK course.school, связь курса с профессией (FK или M2M и related_name), поле цены в месяц, длительность, картинка профессии, логотип школы, флаг активности курса;
   - есть ли get_absolute_url у Course и Profession;
   - какая СУБД (settings.DATABASES): PostgreSQL или SQLite;
   - есть ли уже /search/ в urls.py и строка поиска на главной (form.search в первом экране);
   - имя partial карточки курса каталога.

2. Python (в приложение каталога <app>):
   - app/search_utils.py, app/views_search.py, app/context_processors_search.py, app/templatetags/search_tags.py → в <app>/ (создай __init__.py в templatetags, если нет).
   - Маршруты из app/urls_search.py добавь в urls.py ДО маршрутов вида "<slug>/", имена: "search" и "search_suggest". Если /search/ уже есть — замени его view на search_page, ничего больше не ломая.
   - В views_search.py поправь под мои модели: professions_qs() (имя related_name курсов в Count/Min), courses_qs() (фильтр активных), profession_to_dict / course_to_dict (имена полей картинок, цены, длительности). Если поля нет — оставь getattr(..., None), в подсказке строка просто не выведется.
   - Добавь get_absolute_url туда, где его нет.
   - settings: "<app>.context_processors_search.search_popular" в TEMPLATES context_processors и SEARCH_POPULAR = ["Python", "Дизайнер", "Аналитик данных", "Figma", "Маркетолог", "SQL"] (я поменяю под себя).

3. Поиск по кириллице без учёта регистра:
   - Если база SQLite — ОБЯЗАТЕЛЬНО: добавь SearchTextMixin из app/models_mixin.py к Course и Profession (models_mixin.py положи в <app>/), makemigrations + migrate, скопируй management/commands/rebuild_search_text.py и запусти python manage.py rebuild_search_text. Без этого «ДИЗ» не найдёт «Дизайнер».
   - Если PostgreSQL — миксин не обязателен (icontains работает), но если курсов больше 5 000, тоже добавь его — поиск по индексу быстрее.
   - Если курсы импортируются массово (bulk_create / update без save()) — после импорта вызывай rebuild_search_text, покажи где.

4. Шаблоны и статика:
   - static/edukursy/js/search.js и static/edukursy/css/search.css → в статику. Если полный style.css из пакета edukursy уже подключён — подключи search.css отдельным <link> ПОСЛЕ style.css.
   - templates/edukursy/partials/search_bar.html → base.html сразу после </header> (на ВСЕХ страницах).
   - templates/edukursy/partials/search_scripts.html → base.html перед </body>, после основного script.js.
   - templates/edukursy/search/results.html → страница результатов. Замени include карточки на мой partial карточки курса. Если в base.html нет блока robots — добавь.
   - На главной в первом экране уже есть своя форма поиска (form.search) — оставь её, но поставь ей action="{% url 'search' %}".
   - В макете есть data-suggest-demo и <script id="search-demo"> — это ТОЛЬКО для макета, на сайт НЕ переносить.

5. Тесты: app/tests/test_search_utils.py и test_search_views.py → <app>/tests/. В test_search_views.py поправь функции make_* под обязательные поля моих моделей. Запусти python manage.py test <app>.tests.

6. Проверь руками и покажи результат:
   - фокус в пустом поле → «Часто ищут»; после поиска появляется «Вы искали»;
   - «p» → «Введите ещё 1 букву»; «pyt» → профессии и курсы, совпадение подсвечено синим, внизу «Все результаты по запросу «pyt»» с числом;
   - «ДИЗ» и «диз» дают одинаковый результат; «ghjuh» → «Показаны результаты по запросу «прогр»»;
   - ↑↓ переключают подсказки, Enter открывает выбранную, Esc закрывает, «/» ставит курсор в поиск;
   - Enter без выбора → /search/?q=... с профессиями и курсами, пагинация по 24;
   - на одну подсказку — не больше 4 SQL-запросов (2 count + 2 выборки), при повторе того же запроса — 0 (кэш);
   - ширина 390 px: выпадашка на всю ширину экрана, не уходит за край, кнопка «Найти» видна;
   - подсказки не перекрываются плавающей панелью сравнения и липкой шапкой.

Покажи diff base.html, urls.py, settings.py и моделей перед сохранением.
```

## Если что-то пошло не так

- **Подсказки не появляются** → «Открой в браузере /search/suggest/?q=pyt и покажи ответ. Проверь, что URL с именем search_suggest есть и стоит выше маршрутов со slug.»
- **«ДИЗ» не находит «Дизайнер»** → «База SQLite: добавь SearchTextMixin к моделям, миграцию и запусти rebuild_search_text.»
- **Ошибка FieldError в Count/Min** → «В professions_qs() укажи правильный related_name курсов у Profession.»
- **Выпадашка под другими блоками** → «У .site-search z-index 95, у шапки 100, у панели сравнения 120. Проверь, что у родителя .site-search нет overflow: hidden.»
- **Картинки в подсказках битые** → «В profession_to_dict / course_to_dict используй правильные поля ImageField и MEDIA_URL.»
