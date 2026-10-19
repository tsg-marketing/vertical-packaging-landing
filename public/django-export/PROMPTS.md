# Промпты для Cline — перенос по шагам

Как пользоваться: копируйте промпты по одному в Cline (режим **Plan**, затем **Act**).
Не переходите к следующему шагу, пока текущий не работает и не сверен с макетом.
Перед началом сделайте коммит в git — чтобы любой шаг можно было откатить.

---

## Шаг 0. Подготовка (вручную, без Cline)

1. Распакуйте архив `django-export.zip`.
2. Скопируйте в корень Django-проекта (рядом с `manage.py`):
   - папку `mockups/` и файл `DATA_MAP.md` → в новую папку `_design/`
   - папку `static/edukursy/` → в вашу папку статики (обычно `static/`)
   - файл `.clinerules` → в корень проекта
   - файл `PROMPTS.md` → в `_design/`
3. Проверьте: файл `_design/mockups/courses/index.html` открывается в браузере и выглядит как на макете.

---

## Шаг 1. Аудит проекта и данных (только чтение)

```
Прочитай .clinerules и _design/DATA_MAP.md. Ничего не меняй — только анализ.

1. Изучи структуру Django-проекта: settings (INSTALLED_APPS, TEMPLATES, STATIC*, DATABASES), urls.py, все models.py, существующие шаблоны и base.html.
2. Покажи мне список существующих моделей и их полей (кратко).
3. Пройди по каждой строке таблиц в _design/DATA_MAP.md и заполни колонку «В БД?»:
   - «есть: Model.field», если поле уже есть (учитывай другие названия: title вместо name и т.п.);
   - «вычисл.» — если считается из других полей;
   - «новое» — если нужно добавить;
   - «скрыть» — если данных нет и брать их неоткуда.
   Если не уверен — запусти `python manage.py shell` и посмотри реальные данные: сколько записей, сколько заполнено (например, Course.objects.exclude(old_price=None).count()).
4. Сохрани результат в _design/DATA_AUDIT.md: таблица + список новых полей/моделей + список блоков, которые будут скрыты.
5. Отдельно перечисли конфликты: где у меня структура отличается от макета (например, курс привязан к нескольким профессиям, нет slug у школы и т.п.) и предложи решение.

Жду отчёт, не пиши код.
```

> Проверьте отчёт. Здесь вы решаете, какие поля добавлять, а какие блоки скрыть. Поправьте DATA_AUDIT.md руками, если нужно.

---

## Шаг 2. Модели и миграции

```
По _design/DATA_AUDIT.md добавь недостающие поля и модели.

Правила:
- Существующие поля и таблицы НЕ удалять и НЕ переименовывать.
- Все новые поля: null=True, blank=True (кроме slug — если slug нет, добавь поле, заполни data-миграцией через slugify из name/title с проверкой уникальности, только потом сделай unique).
- Новые модели (если нужны): CourseModule(course FK, order, title, duration, description), CourseUSP(course FK, order, icon, title, text), BlogCategory, BlogPost, Tag, Author, FAQ(page_key, order, question, answer, icon), AdSlot(key, html, is_active).
- Вычисляемые значения НЕ хранить: делай @property или annotate в QuerySet (например, CourseQuerySet.with_price_per_month()).
- Добавь get_absolute_url() для School, Profession, Course, BlogPost по URL-схеме:
  /professions/<slug>/, /courses/<school_slug>/<course_slug>/, /schools/<slug>/, /blog/<slug>/.
- Зарегистрируй новые модели и поля в admin.py (inline для CourseModule и CourseUSP внутри курса).

Покажи план, после подтверждения: makemigrations, покажи SQL миграции (sqlmigrate), затем migrate. Запусти python manage.py check.
```

---

## Шаг 3. Статика и базовый шаблон

```
Создай базовый шаблон для новых страниц по макетам из _design/mockups/.

1. templates/edukursy/base.html:
   - <head>: {% block title %}, {% block meta_description %}, {% block canonical %}, {% block robots %}{% endblock %}, {% block og %}{% endblock %}, подключение {% static 'edukursy/css/style.css' %}.
   - шапка и подвал взять из _design/mockups/courses/index.html (секции «ШАПКА» и «ПОДВАЛ»), пути к картинкам → {% static %}, ссылки меню → {% url %}.
   - Активный пункт меню: aria-current="page" через {% block nav_active %} или переменную nav_active в контексте.
   - {% block content %} внутри <main>.
   - перед </body> — {% static 'edukursy/js/script.js' %}.
   - год в подвале: {% now "Y" %}.
2. Вынеси в templates/edukursy/partials/: header.html, footer.html, breadcrumbs.html (принимает список (title, url)), pagination.html (Django Paginator, сохраняет GET-параметры, повтори разметку nav.pagination из макета: «Назад» disabled на первой странице, многоточия), ad_slot.html (принимает key и вариант: card / sidebar / inline / article — разметка из макетов, если AdSlot неактивен или нет — ничего не выводить), faq.html (список вопросов + FAQPage микроразметка).
3. Если на сайте уже есть свой base.html — НЕ ломай его: новый шаблон сделай отдельным, и сообщи мне, чем они отличаются.

Проверь: python manage.py collectstatic --dry-run без ошибок.
```

---

## Шаг 4. Карточки (общие компоненты)

```
Сделай include-шаблоны карточек в templates/edukursy/partials/cards/, разметку бери 1:1 из макетов:

- course_card.html — article.catalog-card (макет: _design/mockups/schools/school_name/index.html и professions/backend-razrabotchik/index.html). Варианты: с картинкой и без (div.card-thumb--empty card-thumb--tone-N, N = (school.id % 6) + 1, буква — первая буква названия школы). Логотип школы рядом с названием, если есть. Рассрочка: если нет price_month — «Без рассрочки». Старая цена — только если есть.
- school_card.html — карточка школы (макет: schools/index.html).
- profession_tile.html — плитка профессии (макет: professions/index.html).
- post_card.html — article.post-card (макет: blog/index.html).

Все блоки, для которых нет данных, оборачивай в {% if %}. Цены форматируй с пробелами между тысячами (сделай фильтр |rub в templatetags/edukursy.py: 98000 → «98 000 ₽»; используй неразрывный пробел).
```

---

## Шаг 5. Профессии: список и страница профессии

```
Сделай страницы по макетам:
- /professions/ → _design/mockups/professions/index.html
- /professions/<slug>/ → _design/mockups/professions/backend-razrabotchik/index.html

Требования:
- Class-based views (ListView / DetailView) в отдельном приложении или в существующем каталоге — предложи, где лучше.
- Список: фильтры GET area, q (поиск по name, icontains), has_courses; агрегаты courses_count, min_price, duration_range через annotate. Только профессии с курсами, если has_courses=1.
- Страница профессии: курсы этой профессии с фильтрами tag, school, price_min, price_max, kind, сортировка sort (price_asc, price_desc, popular, duration), пагинация 12 на страницу. Счётчики рядом с вариантами фильтров — реальные Count.
- Нативная рекламная карточка встаёт в сетку после 6-й карточки (forloop.counter == 6), сайдбар-реклама — под фильтрами. Не больше рекламных блоков, чем в макете.
- Секции «Кто такой…», «Чему учат», «Похожие профессии», FAQ — выводятся только если есть данные.
- H1: «Курсы {{ name_genitive }}», если нет — «Курсы по профессии {{ name }}».
- canonical без GET-параметров (кроме page).
- select_related/prefetch_related — без N+1 (проверь django-debug-toolbar, если установлен, или connection.queries).

После: открой обе страницы, сравни с макетами на ширине 1440 и 390 px, перечисли расхождения и исправь.
```

---

## Шаг 6. Каталог курсов и страница курса

```
Сделай страницы:
- /courses/ → _design/mockups/courses/index.html
- /courses/<school_slug>/<course_slug>/ → _design/mockups/courses/python-razrabotchik/index.html

Каталог:
- Фильтры GET: profession, school (multi), price_min, price_max, duration (0-3, 3-6, 6-12, 12-plus по duration_months), kind, sort (price_asc, price_desc, popular, new). Пагинация 12.
- Сортировка меняется без кнопки (это уже делает script.js через form.submit), в <noscript> оставь кнопку.
- Активные фильтры («чипы») из макета — с крестиком, ссылка убирает один параметр.

Страница курса:
- Плашки фактов (Длительность, Нагрузка, Формат, Поддержка, Старт, Документ) — каждая выводится только если есть значение. Если плашек нет совсем — скрыть блок.
- Блок цены: цена, старая цена + скидка (вычисл.), рассрочка. Кнопки «Перейти на сайт школы» и «Бесплатный вводный урок» ведут на partner_url (fallback: school.partner_url → school.website). Если ссылки нет — кнопки не выводить. У всех ссылок на школу: rel="sponsored noopener" target="_blank".
- Вкладки (nav.page-tabs) показывают только существующие секции.
- Секции: УТП (CourseUSP), Программа (CourseModule, details/summary), CTA-полоса, «О школе», «Похожие курсы других школ» (та же профессия, другая школа, 4 шт.), реклама (1 блок), FAQ.
- Липкая мобильная кнопка .sticky-cta — тоже на partner_url.
- Микроразметка Course + Offer.
```

---

## Шаг 7. Школы: список и страница школы

```
Сделай страницы:
- /schools/ → _design/mockups/schools/index.html
- /schools/<slug>/ → _design/mockups/schools/school_name/index.html

Список: фильтры q, area, rating_min, license, installment; сортировка rating, courses, price_asc, name; агрегаты courses_count, min_price. Пагинация 12.
Страница школы: шапка (логотип, рейтинг, факты), вкладки, курсы школы с фильтрами profession, price_min, price_max, kind и сортировкой; «О школе» (описание + таблица фактов — каждая строка только если есть значение), перелинковка, FAQ. Блока отзывов НЕТ — не добавляй.
Кнопка «Сайт школы» — school.partner_url или school.website, rel="sponsored noopener".
```

---

## Шаг 8. Сравнение курсов

```
Сделай /compare/ по макету _design/mockups/compare/index.html.

- Набор курсов: GET ?courses=school-slug/course-slug,school-slug/course-slug (до 4). Параметр add добавляет курс, ссылка × убирает (формирует URL без этого курса). Если курсов 0 — пустое состояние: текст «Добавьте курсы для сравнения» и ссылка в каталог.
- Список «Добавить курс»: курсы той же профессии, которых нет в сравнении (до 30, по популярности).
- Таблица: группы строк как в макете. Для каждой строки собери значения; если значения нет — «—» (span.cmp-no). Булевы: «✓ Есть» (span.cmp-yes).
- Подсветка лучшего (td.is-best + span.cmp-best): мин. цена, мин. цена за месяц обучения, макс. проектов, макс. рейтинг школы. Если значения равны у всех — не подсвечивать.
- «Только различия» (diff=1): скрыть строки, где у всех курсов одинаковые значения.
- Итоговые карточки (3 шт.) считаются из тех же данных; если курс один — блок скрыть.
- Все кнопки «На сайт школы» — partner_url с fallback.
- <meta name="robots" content="noindex, follow">.
- Логику сравнения вынеси в отдельный модуль compare.py (функция build_comparison(courses) → строки, лучшие значения, итоги) и покрой простыми тестами.
```

---

## Шаг 8.5. Кнопка «Сравнить» в листинге и на странице курса

```
Добавь возможность выбирать курсы для сравнения из каталога и со страницы курса. Готовые файлы лежат в _design/compare_addon/ — используй их, не пиши с нуля. Эталон вида: _design/mockups/courses/index.html и _design/mockups/courses/python-razrabotchik/index.html (поиск по "COMPARE:").

1. Скопируй файлы (см. _design/compare_addon/README.md):
   - static/edukursy/js/compare.js → в статику;
   - templates/edukursy/partials/compare/*.html → в шаблоны;
   - templatetags/compare_tags.py → в templatetags приложения каталога (если папки нет — создай с __init__.py);
   - context_processors.py → в приложение и добавь "<app>.context_processors.compare" в settings.TEMPLATES[0]["OPTIONS"]["context_processors"].
   - Стили: если style.css из пакета уже подключён — в нём есть блок «КНОПКА «СРАВНИТЬ»». Если у меня свой CSS — подключи static/edukursy/css/compare.css отдельно.
2. Проверь фильтр compare_id: он строит "<school.slug>/<course.slug>". Если у моих моделей поля называются иначе — поправь фильтр и parse_compare_ids, но формат идентификатора оставь «школа/курс».
3. base.html:
   - <body data-compare-url="{% url 'compare' %}"> (имя URL сравнения — как у меня в urls.py);
   - перед </body>, после script.js: {% include "edukursy/partials/compare/scripts.html" %}.
4. Карточка курса (во ВСЕХ местах: каталог, страница профессии, страница школы, «Похожие курсы», главная):
   - кнопка ставится ПЕРВЫМ ребёнком <article class="catalog-card">, ДО ссылки <a class="catalog-card__link"> (кнопка не должна быть внутри <a> — это невалидный HTML и клик уводил бы на курс);
   - {% include "edukursy/partials/compare/button.html" with course=course variant="card" %}
   - если у меня свой шаблон карточки — добавь в его корневой элемент position: relative.
5. Страница курса:
   - в карточке цены (aside.price-box), сразу после кнопки «Бесплатный вводный урок»:
     {% include "edukursy/partials/compare/button.html" with course=course variant="block" label_off="Добавить к сравнению" label_on="Добавлен к сравнению" %}
     {% include "edukursy/partials/compare/link.html" %}
   - в липкой мобильной панели .sticky-cta оберни кнопку «На сайт школы» в <div class="sticky-cta__actions"> и поставь перед ней variant="icon".
   - вариант variant="inline" (в шапке под фактами) — НЕ добавляй, если у меня уже есть кнопка «Сравнить курс» в шапке: замени её на этот include, чтобы не было двух кнопок рядом. На десктопе должно остаться: кнопка в price-box. Кнопку в шапке оставь только если price-box на странице нет.
6. Страница /compare/: возьми логику из compare_addon/compare_view_snippet.py:
   - курсы берутся из ?courses=..., а если параметра нет — из cookie edukursy_compare (сделай redirect на URL с ?courses=, чтобы ссылкой можно было поделиться);
   - в контекст передай compare_state — тогда плавающая панель на этой странице скрыта, а выбор в браузере совпадёт с таблицей;
   - крестик «убрать курс» в таблице должен вести на URL без этого курса (так уже сделано в шаге 8) — compare.js подхватит новый список сам. Когда убирается последний курс, ссылка должна быть /compare/?courses= (с пустым параметром), иначе редирект по cookie вернёт курс обратно.
7. Кэш: если страницы каталога кэшируются целиком (cache_page / nginx), состояние кнопок всё равно восстановит JS при загрузке. Ничего не ломается, но в кэшированных страницах aria-pressed будет "false" до запуска скрипта — это нормально. Заголовок Vary: Cookie добавлять НЕ нужно.
8. Проверь руками:
   - добавь курс в каталоге → кнопка «✓ В сравнении», рамка карточки синяя, снизу появилась панель «Сравнение 1 из 4», в меню у «Сравнения» счётчик 1;
   - добавь 2-й → в панели активна кнопка «Сравнить 2 курса», она ведёт на /compare/?courses=a/b,c/d;
   - 5-й курс не добавляется, появляется подсказка;
   - перезагрузи страницу → состояние сохранилось, кнопки сразу нажаты (без мигания — это работа context processor);
   - открой страницу курса → в price-box «Добавлен к сравнению» и ссылка «Перейти к сравнению 2»;
   - мобильная ширина 390px: панель снизу сворачивается по тапу на заголовок, над липкой кнопкой «На сайт школы», не перекрывает её;
   - работа с клавиатуры: Tab до кнопки, Enter переключает, aria-pressed меняется.
Покажи мне diff шаблонов перед сохранением.
```

---

## Шаг 9. Блог: лента и статья

```
Сделай:
- /blog/ → _design/mockups/blog/index.html
- /blog/<slug>/ → _design/mockups/blog/kak-sravnivat-ceny-kursov/index.html

Лента: рубрики (?category=slug, со счётчиками), главная статья (is_featured, иначе самая свежая — и её не дублировать в сетке), сетка 9 на страницу, нативная реклама после 3-й карточки, широкий баннер после пагинации. Рекламных блоков на странице — не больше 2.
Статья:
- Тело — post.body через |safe (контент только из админки). Если в проекте есть редактор (CKEditor/TinyMCE) — используй его.
- Оглавление: распарси <h2> из body (BeautifulSoup или regex), проставь id, если нет (slugify). Если h2 меньше 3 — оглавление скрыть.
- Время чтения: слова / 200, минимум 1.
- Реклама: блок 1 вставляется в тело после ~40% h2 (после второго h2 из пяти и т.п.), блок 2 — после статьи. Всего 2.
- «Курсы по теме» внутри статьи — курсы с общими тегами (до 3), если нет — не выводить.
- «Читайте также» — 3 статьи той же рубрики, кроме текущей.
- Микроразметка Article, Open Graph.
```

---

## Шаг 9.5. Главная страница

```
Сделай главную страницу / по макету _design/mockups/index.html. Прочитай раздел «7. Главная страница» в _design/DATA_MAP.md.

ВАЖНО: на сайте уже может быть своя главная. Сначала найди текущий view и шаблон для "/" (urls.py) и покажи мне. НЕ удаляй её: новый шаблон сделай templates/edukursy/home.html, новый view — HomeView. Переключение URL "/" — только после моего подтверждения (до этого повесь новую главную на /new-home/ для проверки).

Секции (разметка 1:1 из макета, наследуй base.html, шапку/подвал — из partials):
1. Первый экран: заголовок, поиск (GET; если отдельного поиска нет — action="{% url 'courses' %}" с параметром q и обработай q в каталоге), счётчики курсов/школ/профессий (Count, кэшировать через django cache на 1 час).
2. Виджет «Подбор курса»: GET-форма на каталог /courses/. Профессии — из БД. Поля level, duration (short ≤3 мес, mid 3–9, long >9), price_max, certificate, installment, mentor — каталог должен их понимать; если соответствующего поля в модели нет — убери этот фильтр из формы (не оставляй нерабочих чекбоксов). Ползунок бюджета уже работает через script.js (#pk-budget).
3. Популярные профессии: 8–12 шт. (по Profession.order или по числу курсов), annotate courses_count, min_price. Карточка article.profession-card.
4. Реклама after_professions — partials/ad_slot.html.
5. Популярные курсы: 6–12 шт. (is_featured, иначе по популярности), select_related('school'). Карточка article.course-card — вынеси в partials/cards/course_card_big.html. Рейтинг, отзывы, формат, старая цена, рассрочка — каждое в {% if %}.
6. «Как это работает» и «Как мы сравниваем» — статично в шаблоне.
7. Реклама native_middle.
8. Школы: все активные школы с courses_count и min_price.
9. Блог: 3 последние статьи (partials/cards/post_card.html). Нет статей — секцию скрыть.
10. SEO-текст (класс prose prose--wide) — статично или из SiteText, FAQ — из FAQ(page_key="home") или статично, с микроразметкой FAQPage.
11. Реклама bottom_wide.

Общее число SQL-запросов на главной — не больше 12 (проверь). Title, description и canonical "https://<домен>/" — через блоки base.html. Добавь Organization + WebSite (SearchAction) в JSON-LD.

После: сравни с макетом на 1440 и 390 px и перечисли отличия.
```

---

## Шаг 10. Карта сайта, редиректы, финальная проверка

```
1. Добавь страницы в sitemap.xml (django.contrib.sitemaps): профессии, курсы, школы, статьи. /compare/ с параметрами — не добавлять.
2. Проверь robots.txt: не закрыты ли новые разделы.
3. Если раньше эти разделы жили по другим адресам — сделай 301-редиректы.
4. Пройди все страницы: / (главная), /professions/, /professions/<slug>/, /courses/, /courses/<school>/<course>/, /schools/, /schools/<slug>/, /compare/?courses=..., /blog/, /blog/<slug>/.
   Для каждой: нет ошибок 500, нет «None»/пустых плашек, нет N+1 (число SQL-запросов ≤ 15), вёрстка совпадает с макетом на 1440 и 390 px.
5. Удали из шаблонов все оставшиеся <!-- DATA --> комментарии.
6. Составь короткий отчёт: что сделано, какие блоки скрыты из-за отсутствия данных, какие поля нужно заполнить в админке.
```

---

## Если что-то пошло не так

- **Вёрстка «поехала»** → «Сравни разметку шаблона X с _design/mockups/X/index.html построчно: какие классы и обёртки отличаются? Исправь, CSS не трогай.»
- **Cline хочет переписать CSS** → «Не меняй style.css. Найди класс в макете и используй его.»
- **Ошибка миграции на живой БД** → «Откати последнюю миграцию (migrate app <предыдущий_номер>), сделай поле nullable и раздели на 2 миграции: схема + data-миграция.»
- **Медленная страница** → «Покажи все SQL-запросы этой страницы и убери N+1 через select_related/prefetch_related/annotate.»
