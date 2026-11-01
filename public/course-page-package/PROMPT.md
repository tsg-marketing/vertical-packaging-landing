# Промпт для агента: страница курса из extract_json + editorial_json

Перед запуском:
1. Коммит в git и резервная копия базы (может понадобиться миграция).
2. Распакуйте архив, папку `course-page-package/` положите в корень Django-проекта как `_design/course-page-package/`.
3. Откройте `_design/course-page-package/mockups/courses/kurs-json/index.html` и `mockups/courses/kurs-json-partial/index.html` — так должно получиться.

Запускайте **двумя частями** в одной задаче, режим **Plan → Act**. Вторую часть — после проверки первой.

---

## Часть 1 из 2 — данные и админка

```
Задача: страница курса = лендинг (текущие поля курса) + разбор редакции из двух JSON-полей курса: extract_json и editorial_json. Готовые файлы — в _design/course-page-package/, сначала прочитай README.md целиком. Используй файлы пакета, не пиши с нуля. В этой части — только модель, логика и админка. Шаблоны сайта не трогай.

1. Изучи и покажи кратко:
   - модель Course (приложение — назову <app>): есть ли уже поля extract_json и editorial_json, какого они типа (JSONField или TextField), null/blank/default;
   - как зарегистрирован CourseAdmin: fields/fieldsets, list_display, list_filter, свои formfield_for_dbfield / save_model / get_readonly_fields;
   - view страницы курса (рендерит edukursy/courses/detail.html): что кладёт в контекст (course, faqs, facts, usps, modules, partner_url, price_month, similar…);
   - СУБД (PostgreSQL или SQLite).

2. Поля:
   - Если полей нет — добавь в Course:
       extract_json = models.JSONField("Факты со страницы школы (extract_json)", default=dict, blank=True)
       editorial_json = models.JSONField("Текст редакции (editorial_json)", default=dict, blank=True)
     и сделай миграцию.
   - Если поля есть и это TextField со строками JSON — НЕ меняй тип без моего согласия. Покажи, сколько курсов с непустым значением и сколько из них невалидный JSON (python manage.py shell, parse_json из course_json.py). Предложи миграцию TextField → JSONField с переносом данных (RunPython: parse_json, при ошибке — {} и вывод id курса в консоль) и жди моего «да».
   - Если это уже JSONField — ничего не меняй.

3. Логика: app/course_json.py → <app>/course_json.py, app/templatetags/course_json.py → <app>/templatetags/ (создай __init__.py, если нет). Не переименовывай ключи — они совпадают с моими промптами-схемами в _design/course-page-package/schemas/.

4. Админка:
   - app/admin_course_json.py → <app>/; app/templates/course_page/ → <app>/templates/course_page/; static/admin/course_page/ → static/admin/course_page/.
   - В CourseAdmin: CourseJsonAdminMixin ПЕРВЫМ в наследовании; CourseJsonAdminMixin.json_fieldset — в fieldsets после основных полей (если используются fields — переведи на fieldsets, сохранив порядок); "json_status_col" — в list_display; JsonStatusFilter — в list_filter.
   - Если у CourseAdmin свои formfield_for_dbfield, save_model или get_readonly_fields — объедини через super(), покажи diff.
   - Если extract_json/editorial_json — TextField (я не согласился на миграцию), поле формы всё равно должно работать: JsonDictField возвращает dict — для TextField сохраняй json.dumps(..., ensure_ascii=False). Покажи, как сделал.
   - JsonStatusFilter использует __has_key — на SQLite он работает с Django 4.2+. Если у меня ниже — скажи.

5. Тесты: app/tests/test_course_json.py и app/tests/samples/ → <app>/tests/. Запусти python manage.py test <app>.tests.test_course_json — 16 из 16.

6. Проверь в админке и покажи скриншоты:
   - в карточке курса раздел «Разбор курса (JSON)»: вставь samples/extract_full.json и samples/editorial_full.json → «JSON корректный…», «Форматировать» работает;
   - вставь JSON в обёртке ```json … ``` — сохраняется без обёртки;
   - вставь {"certificate":"да", } — не сохраняется, понятная ошибка со строкой и позицией;
   - вставь {"certificate":"да"} — не сохраняется: «ожидается true, false или null»;
   - после сохранения «Что выведется на странице» — «Блоков на странице: 15 из 15»; с extract_partial/editorial_partial — меньше, у пропущенных «—»;
   - в списке курсов колонка «Разбор» с бейджами и фильтр «Разбор (JSON)».
```

---

## Часть 2 из 2 — шаблон страницы курса

```
Часть 2: шаблон страницы курса. Эталон — _design/course-page-package/mockups/courses/kurs-json/index.html (все блоки) и mockups/courses/kurs-json-partial/index.html (часть данных).

1. templates/edukursy/courses/detail.html из пакета — это МОЙ текущий detail.html, в который встроены блоки из JSON. Сравни его с моим действующим templates/edukursy/courses/detail.html (diff). Если мой изменился после того, как я отправил его тебе, — перенеси мои изменения в новую версию, ничего не теряя. Покажи итоговый diff перед сохранением.
2. templates/edukursy/courses/blocks/ → в шаблоны (10 файлов).
3. static/edukursy/css/course-page.css → в статику, подключи в base.html ПОСЛЕ podborki.css: <link rel="stylesheet" href="{% static 'edukursy/css/course-page.css' %}">
4. View страницы курса: добавь в контекст cpage = course_page_for(course, faqs) (from <app>.course_json import course_page_for), где faqs — тот же список, что уже передаётся в шаблон. Если faqs нет в контексте — передай None. Тег {% course_page %} в шаблоне — запасной вариант, если cpage не передан.
5. Шаблон использует мои теги и фильтры: {% load edukursy %}, rub, plural, scope_css, banner, partials compare/button.html, compare/link.html, breadcrumbs.html, cards/course_card.html — проверь, что все существуют, ничего нового не придумывай.
6. FAQ: вопросы из JSON выводятся после FAQ из админки; вопросы, совпадающие с админскими, не повторяются. Скрипт раскрытия FAQ у меня уже работает по .faq-item__btn — проверь, что раскрываются и новые.
7. SEO: meta description берёт editorial_intro / short_summary, если они есть (до 158 символов), иначе — как было. Микроразметка Course и FAQPage должна остаться валидной.
8. Проверь на 4 курсах и покажи скриншоты при 1440 и 390 px:
   - курс с samples/extract_full.json + editorial_full.json → все блоки как в mockups/courses/kurs-json/index.html, в навигации есть «О курсе», «Чему вы научитесь», «Кому подойдёт», «Обучение», «Мнение редакции», «Что уточнить», «Вопросы»;
   - курс с extract_partial + editorial_partial → нет блоков «О курсе», «Как проходит обучение», плюсов, вердикта, FAQ — и их пунктов в навигации; если у курса нет цены — справа «Стоимость курса 14 900 ₽» из price_text;
   - курс без JSON → страница выглядит ровно как раньше (сравни HTML до и после — разница только в подключении course-page.css);
   - курс с extraction_status "failed" → блоки из extract не выводятся;
   - нет пустых заголовков, пустых <ul> и пустых секций; нет ошибок в консоли браузера; число SQL-запросов на странице не выросло.
```

---

## Если что-то пошло не так

- **TemplateSyntaxError: 'course_json' is not a registered tag library** → «Положи templatetags/course_json.py в <app>/templatetags/, проверь __init__.py и перезапусти сервер.»
- **В админке обычное поле JSON без кнопок и проверки** → «CourseJsonAdminMixin должен стоять первым в наследовании CourseAdmin, а свой formfield_for_dbfield — вызывать super().»
- **Ошибка «Неверный формат» на JSON, который отдала нейросеть** → «Покажи текст ошибки: если это булево в кавычках ("true") или level не из списка — поправь промпт нейросети по схеме из schemas/, а не проверку.»
- **Блок не появляется, хотя данные есть** → «Открой «Что выведется на странице» в админке: проверь, что ключ называется точно как в схеме и статус не failed.»
- **Вёрстка блоков «съехала»** → «Проверь, что course-page.css подключён после style.css и что в style.css есть .section, .section-head, .prose, .page-tabs.»
- **Повторяются вопросы в FAQ** → «Передай в course_page_for тот же список faqs, что выводится в шаблоне.»
