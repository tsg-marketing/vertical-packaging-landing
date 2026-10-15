# Карта данных: что нужно каждой странице

В макетах (`mockups/`) все динамические места помечены комментариями `<!-- DATA: ... -->`.
Ниже — сводная таблица этих полей. Колонка **«В БД?»** заполняется на шаге 1 (аудит):
Cline сравнивает поля с существующими моделями и проставляет:

- `есть` — поле уже есть в модели (указать `Model.field`);
- `вычисл.` — считается из других полей (агрегат, annotate, property);
- `новое` — нужно добавить в модель + миграция (по умолчанию `null=True, blank=True`);
- `конфиг` — не данные БД, а настройка (settings / константа / шаблон);
- `скрыть` — данных нет и не будет: блок в шаблоне оборачивается в `{% if %}` и не выводится.

**Главное правило:** если значения нет — блок не выводится целиком (вместе с подписью).
Никаких «—», «0 ₽», «None» и пустых плашек на сайте.

---

## 1. Школа (`school`)

| Поле в макете | Тип | Где используется | Обяз. | В БД? | Если нет данных |
|---|---|---|---|---|---|
| school.name | str | везде | да | | — |
| school.slug | slug | URL `/schools/<slug>/` | да | | сгенерировать из name |
| school.logo | image | карточки, шапка школы | нет | | `div.card-thumb--empty` с первой буквой |
| school.rating | decimal(3,2) | список, страница школы, курс, сравнение | нет | | скрыть звезду и число |
| school.reviews_count | int | шапка школы | нет | | скрыть |
| school.founded | int (год) | список, курс | нет | | скрыть |
| school.short_description | text | шапка школы, блок «О школе» на курсе | нет | | скрыть абзац |
| school.description | text/HTML | «О школе» | нет | | скрыть секцию |
| school.website | url | кнопка «Сайт школы» | нет | | скрыть кнопку |
| school.partner_url | url | все кнопки «На сайт школы» (если у курса нет своей) | нет | | fallback → school.website |
| school.license | bool | фильтр, «О школе» | нет | | скрыть строку |
| school.certificate | str | «О школе» | нет | | скрыть строку |
| school.refund | str | «О школе» | нет | | скрыть строку |
| school.installment | str/bool | фильтр, «О школе» | нет | | скрыть строку |
| school.tax_deduction | bool | «О школе» | нет | | скрыть строку |
| school.legal_name | str | «О школе» (юрлицо, ИНН) | нет | | скрыть строку |
| school.formats | M2M/список | плашки форматов | нет | | скрыть |
| school.areas | M2M Area | фильтр «Направление» | нет | | — |
| school.courses_count | int | везде | — | вычисл. | `Count('courses')` |
| school.min_price | int | список, шапка | — | вычисл. | `Min('courses__price')` |
| school.checked_at | date | «Данные проверены» | нет | | скрыть |

## 2. Профессия (`profession`)

| Поле в макете | Тип | Где | Обяз. | В БД? | Если нет данных |
|---|---|---|---|---|---|
| profession.name | str | везде | да | | — |
| profession.slug | slug | URL `/professions/<slug>/` | да | | — |
| profession.name_genitive | str | H1 «Курсы Backend-разработчика» | нет | | fallback: «Курсы по профессии {name}» |
| profession.area | FK Area | фильтр, надзаголовок | нет | | скрыть |
| profession.icon | str (эмодзи) | плитка | нет | | первая буква name |
| profession.lead | text | шапка | нет | | скрыть |
| profession.description | text/HTML | «Кто такой…» | нет | | скрыть секцию |
| profession.skills | JSON / модель | «Чему учат» | нет | | скрыть секцию |
| profession.facts | JSON | справка справа (языки, инструменты) | нет | | скрыть |
| profession.related | M2M self | «Похожие профессии» | нет | | скрыть колонку |
| profession.courses_count | int | везде | — | вычисл. | |
| profession.schools_count | int | шапка | — | вычисл. | |
| profession.min_price | int | шапка, плитка | — | вычисл. | |
| profession.duration_range | str | шапка, плитка | — | вычисл. | `Min/Max(duration_months)` |

## 3. Курс (`course`)

| Поле в макете | Тип | Где | Обяз. | В БД? | Если нет данных |
|---|---|---|---|---|---|
| course.name | str | везде | да | | — |
| course.slug | slug | URL `/courses/<school>/<course>/` | да | | — |
| course.school | FK | везде | да | | — |
| course.profession | FK/M2M | крошки, фильтр | да | | — |
| course.kind | choice: profession/course | надпись над названием, фильтр | нет | | скрыть надпись |
| course.image_url | image | карточка | нет | | `div.card-thumb--empty card-thumb--tone-N` |
| course.price | int | везде | да | | «Цена на сайте школы» |
| course.old_price | int | зачёркнутая цена | нет | | скрыть `<s>` |
| course.discount_percent | int | плашка −30% | — | вычисл. | из price/old_price |
| course.price_month | int | рассрочка | нет | | «Без рассрочки» (как в макете) |
| course.installment_months | int | «в рассрочку на N мес» | нет | | скрыть хвост фразы |
| course.duration / duration_months | int | везде | нет | | скрыть |
| course.hours_per_week | str | плашка «Нагрузка» | нет | | скрыть плашку |
| course.hours_total | int | «7 модулей · 320 часов» | нет | | скрыть часы |
| course.format | str | плашка «Формат» | нет | | скрыть |
| course.support | str | плашка «Поддержка» | нет | | скрыть |
| course.mentor | str/bool | сравнение | нет | | `—` в таблице сравнения (единственное место, где прочерк допустим) |
| course.homework_review | str | сравнение | нет | | `—` |
| course.projects_count | int | сравнение | нет | | `—` |
| course.final_project | bool | сравнение | нет | | `—` |
| course.free_lesson | bool | сравнение | нет | | `—` |
| course.tax_deduction | bool | сравнение | нет | | fallback → school.tax_deduction |
| course.start_date | date/str | плашка «Старт» | нет | | скрыть |
| course.certificate | str | плашка «Документ» | нет | | fallback → school.certificate |
| course.short_description | text | шапка курса | нет | | скрыть |
| course.tags | M2M Tag | плашки, фильтр `tag` | нет | | скрыть |
| course.partner_url | url | ВСЕ кнопки «На сайт школы» | нет | | fallback → school.partner_url → school.website; если нет ничего — кнопки скрыть |
| course.checked_at | date | «Цена проверена» | нет | | скрыть |
| course.modules | модель CourseModule (title, duration, description, order) | «Программа» | нет | | скрыть секцию и вкладку |
| course.modules_count | int | «7 модулей» | — | вычисл. | |
| course.usp | модель CourseUSP (icon, title, text, order) | «Почему стоит выбрать» | нет | | скрыть секцию и вкладку |
| course.price_per_month_of_study | int | сравнение | — | вычисл. | price / duration_months |
| course.popularity / created_at | int/date | сортировка popular / new | нет | | сортировка по id |

## 4. Сравнение (`/compare/`)

| Поле | Тип | Где | В БД? | Примечание |
|---|---|---|---|---|
| compare.courses | список из GET `?courses=school/course,...` | таблица | конфиг | до 4 курсов, одна профессия |
| compare.count | int | подзаголовок | вычисл. | |
| compare.profession | str | подзаголовок | вычисл. | профессия первого курса |
| compare.checked_at | date | подзаголовок | вычисл. | `min(course.checked_at)` |
| is-best | — | подсветка ячейки | вычисл. | min цены, min цены/мес, max проектов, max рейтинга |
| pick.label / pick.reason | str | итоговые карточки | вычисл. | 3 итога: дешевле всего / больше практики / выше рейтинг; текст по шаблону |
| CompareSet (опц.) | модель: slug, title, courses M2M | готовые подборки `/compare/<slug>/` | новое | можно сделать позже |

## 5. Блог

| Поле | Тип | Где | Обяз. | В БД? | Если нет |
|---|---|---|---|---|---|
| post.title | str | везде | да | | |
| post.slug | slug | URL `/blog/<slug>/` | да | | |
| post.category | FK Category(name, slug) | плашка, фильтр, крошки | нет | | скрыть |
| post.cover | image | карточка, статья | нет | | `card-thumb--empty` |
| post.cover_alt | str | alt обложки | нет | | = title |
| post.excerpt | text | карточка, лид | нет | | первые 160 символов body без тегов |
| post.body | HTML | статья | да | | |
| post.published_at | datetime | везде | да | | |
| post.updated_at | datetime | статья | — | | `auto_now` |
| post.read_time | int | «9 мин» | — | вычисл. | слов в body / 200 |
| post.is_featured | bool | главная статья ленты | нет | | последняя по дате |
| post.tags | M2M Tag | теги | нет | | скрыть |
| post.author | FK Author(name, role, avatar) | шапка статьи | нет | | «Редакция edukursy.ru» |
| post.seo_title / seo_description | str | `<title>`, meta | нет | | title / excerpt |
| оглавление | — | слева | вычисл. | | из `<h2 id>` в body; если h2 < 3 — скрыть |
| связанные курсы | — | вставка в статью | вычисл. | | курсы по общим тегам; если нет — скрыть |

## 6. Справочники и настройки

| Что | Где | Тип |
|---|---|---|
| Area (Направление: it, design, marketing, management) | фильтры | модель: name, slug |
| Format (онлайн, записи, вебинары…) | плашки | модель или choices |
| FAQ на каждой странице | секция FAQ | модель FAQ(page_key, question, answer, icon, order) или статично в шаблоне |
| SEO-тексты / link-columns | перелинковка | можно статикой в шаблоне на первом этапе |
| Рекламные слоты (AD SLOT) | реклама | модель AdSlot(key, html, is_active) или include-шаблон |
| current_year | подвал | `{% now "Y" %}` |
| Ссылки меню / подвала | шапка, подвал | `{% url %}` |

## 7. Главная страница (`/`)

Макет: `mockups/index.html`. Секции сверху вниз и откуда брать данные:

| Секция | Поля в макете | Источник | Если нет данных |
|---|---|---|---|
| Первый экран + поиск | stats.courses_total, stats.schools_total, stats.professions_total | вычисл. (`Count` по моделям, кэш 1 час) | скрыть счётчик |
| Поиск (`form.search`, GET `/search/?q=`) | — | view поиска | если поиска нет — action на `/courses/?q=` |
| Виджет «Подбор курса» (GET → `/courses/`) | profession, level (zero/base/pro), duration (short/mid/long), price_max, certificate, installment, mentor; picker.found_count | профессии — из БД; found_count — вычисл. | поле, которого нет в модели, — убрать из формы (и в каталоге его не обрабатывать) |
| Популярные профессии (8–12) | profession.name, image, courses_count, min_price, min_price_month, url | Profession + annotate | нет картинки → `card-thumb--empty`; нет min_price_month → скрыть строку |
| Реклама after_professions | — | AdSlot | не выводить |
| Популярные курсы (6–12) | course.name, image, school.name, school.logo, rating, reviews_count, duration, format, price, old_price, price_month, old_price_month, url | Course (по popularity или флаг `is_featured`) | rating/reviews/формат/старая цена — скрыть по отдельности |
| Как это работает | — | статично в шаблоне | — |
| Реклама native_middle | — | AdSlot | не выводить |
| Школы в каталоге | school.name, logo, rating, reviews_count, courses_count, min_price, url | School + annotate | скрыть рейтинг/отзывы по отдельности |
| Как мы сравниваем | — | статично | — |
| Блог (3–6 последних) | post.title, image, category, date, excerpt, url | BlogPost | если статей нет — скрыть секцию |
| SEO-текст | — | статично или модель SiteText(key="home_seo") | — |
| FAQ | вопросы | FAQ(page_key="home") или статично | — |
| Реклама bottom_wide | — | AdSlot | не выводить |

Новые поля, которые могут понадобиться только для главной: `Course.is_featured`, `Course.rating`, `Course.reviews_count`, `Course.old_price_month`, `Course.level` (zero/base/pro), `Profession.image`, `Profession.order`.
