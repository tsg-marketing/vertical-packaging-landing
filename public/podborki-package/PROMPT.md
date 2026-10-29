# Промпт для Cline: подборки курсов (меню до 3 уровней + админка)

Перед запуском:
1. Сделайте коммит в git и **резервную копию базы** — будет миграция.
2. Распакуйте архив, папку `podborki-package/` положите в корень Django-проекта как `_design/podborki-package/`.
3. Откройте в браузере `_design/podborki-package/mockups/index.html` (наведите на «Подборки курсов») и `mockups/admin-demo/index.html` — так должно получиться.

Задача большая — запускайте **тремя частями** в одной задаче Cline, режим **Plan → Act** для каждой.
Следующую часть отправляйте, только когда предыдущая проверена.

---

## Часть 1 из 3 — модель и админка

```
Внедри подборки курсов (теги с иерархией до 3 уровней). Готовые файлы — в _design/podborki-package/, сначала прочитай README.md целиком. Используй файлы пакета, не пиши с нуля. В этой части — ТОЛЬКО модель и админка, сайт не трогай.

1. Изучи и покажи кратко: приложение с моделью Course (назову его <app>), есть ли у Course поле is_active и цена, как зарегистрирован CourseAdmin (декоратор или admin.site.register, какие fields/fieldsets/list_display/list_filter), есть ли уже модель тегов/категорий курсов. Если похожая модель уже есть — СТОП, покажи её и спроси меня, мигрировать её или делать новую.

2. Модель:
   - app/models_tags.py → <app>/models_tags.py. В <app>/models.py: from .models_tags import CourseTag (импорт — до класса Course).
   - В Course добавь: tags = models.ManyToManyField("CourseTag", blank=True, related_name="courses", verbose_name="Подборки")
   - В settings: PODBORKI_TAG_MODEL = "<app>.CourseTag"
   - app/podborki_services.py → <app>/. Если у Course нет is_active — ничего не меняй, visible_courses это учитывает.
   - makemigrations <app> → покажи миграцию → migrate.

3. Админка:
   - app/admin_tags.py, app/widgets_tags.py → <app>/. В admin_tags.py строка "from .models import CourseTag" — оставь как есть.
   - app/templates/podborki/ → <app>/templates/podborki/ (шаблоны виджета).
   - templates/admin/podborki/ → в templates/admin/podborki/ проекта.
   - static/admin/podborki/ → в static/admin/podborki/.
   - В <app>/admin.py: импортируй admin_tags (он сам регистрирует CourseTagAdmin) и добавь в CourseAdmin:
       class CourseAdmin(CourseTagsAdminMixin, admin.ModelAdmin)   ← миксин ПЕРВЫМ
       "tags" — в fields или в отдельный fieldset ("Подборки", {"fields": ("tags",)})
       "tags_col" — в list_display
       TagTreeFilter — в list_filter
     Если у CourseAdmin свой get_queryset, formfield_for_manytomany, get_actions или action_form — объедини с миксином через super(), покажи diff.
   - Если в CourseAdmin tags попадает в filter_horizontal/autocomplete_fields/raw_id_fields — убери оттуда.

4. Тестовые данные: app/management/commands/load_podborki_demo.py → <app>/management/commands/ и запусти python manage.py load_podborki_demo.

5. Тесты: app/tests/test_podborki.py → <app>/tests/. Поправь make_course() под обязательные поля моего Course и School. Запусти python manage.py test <app>.tests.test_podborki — должны пройти все 19 (кроме PagesTests — они заработают в части 2, их пока можно пропустить через -k).

6. Проверь в админке и покажи мне:
   - «Подборки курсов»: дерево 23 подборок с отступами и «ур. 1/2/3»; ↑↓ и перетаскивание за ⋮⋮ меняют порядок только внутри одного родителя, после перезагрузки порядок сохранился;
   - у пустых подборок без вложенных — 🗑, у остальных — 🔒 с причиной при наведении;
   - удаление подборки с курсом или с вложенными → страница «Удалить нельзя», подборка НЕ удалена; массовое удаление пропускает такие с сообщением;
   - форма: в «Родитель» нет подборок 3-го уровня и самой подборки; попытка вложить 4-й уровень — понятная ошибка;
   - карточка курса: поле «Подборки» деревом с чекбоксами, поиск, чипы с путём; отметил «С трудоустройством › Трудоустройство сразу › В IT» — сохранилось, родители помечены полоской, но не отмечены;
   - список курсов: колонка «Подборки», фильтр «Подборка», действия «Добавить в подборку…» / «Убрать из подборки…».
```

---

## Часть 2 из 3 — страницы подборок

```
Часть 2: страницы подборок на сайте. Эталон: _design/podborki-package/mockups/podborki/ (index.html и вложенные папки). Карточки курсов — мой существующий partial карточки каталога.

1. app/views_podborki.py → <app>/. Маршруты из app/urls_podborki.py — в urls.py ДО общих маршрутов со slug; имена "podborki" и "podborka". Если у меня есть маршрут вида "<slug:...>/", который может перехватить "podborki/", — покажи и поставь мои маршруты выше.
2. templates/edukursy/podborki/index.html и detail.html → в шаблоны. Замени include "edukursy/partials/cards/course_card.html" на мой partial карточки курса. Если в base.html нет блоков meta_description или canonical — добавь их, не ломая существующие страницы.
3. Если у Course есть поле популярности с другим именем — добавь его в Course_default_order во views_podborki.py. Сортировки по цене — по моему полю цены (поправь SORTS).
4. static/edukursy/css/podborki.css → в статику, подключи в base.html ПОСЛЕ основного style.css.
5. Карточка курса в подборке должна быть ровно той же, что в каталоге (с кнопкой «Сравнить», если она у меня есть).
6. В sitemap.xml (если есть django.contrib.sitemaps) — добавь активные подборки: CourseTag.objects.filter(is_active=True), location = get_absolute_url.
7. Запусти все тесты из test_podborki.py — 19 из 19.
8. Проверь и покажи:
   - /podborki/ — карточки 1-го уровня, внутри 2-й и 3-й с числами;
   - /podborki/s-trudoustrojstvom/ — курсы из всех вложенных подборок без дублей, чипы «Все · Трудоустройство сразу · После стажировки · С гарантией»;
   - /podborki/s-trudoustrojstvom/srazu/v-it/ — крошки из 4 звеньев, чип «← Все: Трудоустройство сразу» и соседние;
   - сортировка и пагинация сохраняют друг друга в URL;
   - скрытая подборка и подборка со скрытым родителем — 404; /podborki/a/b/c/d/ — 404;
   - на странице подборки не больше 6 SQL-запросов (без учёта карточек курса).
```

---

## Часть 3 из 3 — пункт меню

```
Часть 3: пункт «Подборки курсов» в главном меню. Эталон: _design/podborki-package/mockups/index.html — меню между «Курсы» и «Школы» (поиск по "PODBORKI:").

1. templates/edukursy/partials/podborki_menu.html и podborki_icon.html → в шаблоны. app/templatetags/podborki_tags.py → <app>/templatetags/ (создай __init__.py, если нет).
2. В base.html (и во всех шаблонах, где меню продублировано, — найди grep "Курсы</a>") сразу после пункта «Курсы» внутри <nav class="main-nav"><ul>:
     {% load podborki_tags %}{% podborki_menu %}
   Тег уже знает текущую страницу и подсвечивает пункт на /podborki/....
3. static/edukursy/js/podborki.js → в статику, подключи в base.html перед </body> после основного script.js. Стили меню уже в podborki.css из части 2.
4. Если в шапке у меня свой бургер/скрипт меню — проверь, что открытие подменю не закрывает бургер (podborki.js вешает обработчики только на [data-nav-drop]).
5. Кэш меню: убедись, что CACHES настроен (хотя бы LocMemCache). Сброс кэша уже вызывается при сохранении/удалении подборки и при действиях с курсами в админке. Если курсы меняются ещё где-то (импорт, API, сигналы) — после изменения tags вызывай podborki_services.invalidate_menu_cache(). В apps.py приложения в ready() вызови from .models_tags import connect_course_tags_signal; connect_course_tags_signal() — он сбрасывает кэш при любом изменении Course.tags.
6. Проверь и покажи (скриншоты при ширине 1440, 900 и 390 px):
   - компьютер: наведение на «Подборки курсов» → слева 1-й уровень с иконками, справа 2-й и 3-й уровни; «Бесплатные» — без стрелки, сразу с числом; меню не закрывается при переводе мыши с пункта на панель;
   - телефон: в бургере «Подборки курсов» раскрывается аккордеоном, стрелка у подборки раскрывает её уровни, тап по названию — переход;
   - клавиатура: Tab до пункта, ↓ открывает, ↑↓ по 1-му уровню, → в панель, Esc закрывает;
   - подборки без курсов и с «Не показывать в меню» в меню отсутствуют, на /podborki/ — тоже нет пустых карточек;
   - на любой странице меню добавляет 0 SQL-запросов при повторном открытии (кэш) и 2 — при холодном.
Покажи diff base.html.
```

---

## Если что-то пошло не так

- **makemigrations ругается на related_name «courses»** → «У Course уже есть related_name courses на другой модели — переименуй related_name в CourseTag-связи на "tagged_courses" и замени .courses на .tagged_courses в models_tags.py, podborki_services.py и admin_tags.py.»
- **В карточке курса обычный список вместо дерева** → «Проверь, что CourseTagsAdminMixin стоит первым в наследовании CourseAdmin и что tags нет в filter_horizontal.»
- **Перетаскивание не сохраняется** → «Открой консоль браузера на списке подборок: должен быть POST на …/coursetag/reorder/ с ответом {"ok": true}. Проверь CSRF и что podborki-admin.js подключился.»
- **Подборку с курсами всё равно удалось удалить** → «Проверь, что models_tags.py импортируется при старте (сигнал pre_delete). Запусти DeleteTests.»
- **Меню не обновляется после изменений** → «Вызови invalidate_menu_cache() в месте, где меняются курсы или подборки, и проверь настройку CACHES.»
- **В меню на компьютере подменю уезжает за экран** → «.nav-drop__menu позиционируется fixed по центру экрана под шапкой. Проверь, что у шапки нет transform/filter — они ломают fixed.»
