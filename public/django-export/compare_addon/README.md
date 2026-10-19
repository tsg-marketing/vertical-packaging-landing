# Кнопка «Сравнить» — файлы для Django

| Файл | Куда положить |
|---|---|
| static/edukursy/js/compare.js | static/edukursy/js/ |
| templates/edukursy/partials/compare/*.html | templates/edukursy/partials/compare/ |
| templatetags/compare_tags.py | <ваше_приложение>/templatetags/ |
| context_processors.py | <ваше_приложение>/ + добавить в settings TEMPLATES → OPTIONS → context_processors |
| compare_view_snippet.py | логику перенести во view /compare/ |

Стили уже в общем static/edukursy/css/style.css (раздел «КНОПКА СРАВНИТЬ»).

Как работает:
- Выбор хранится в браузере (localStorage) и дублируется в cookie `edukursy_compare` = "school/course,school/course".
  Без авторизации и без запросов к серверу; база данных не нужна.
- Сервер читает cookie → кнопки сразу рендерятся с aria-pressed="true", без мигания.
- Максимум 4 курса. При попытке добавить 5-й — подсказка.
- Плавающая панель снизу появляется после первого добавленного курса: чипы курсов, «Очистить», «Сравнить N курса».
- В меню у пункта «Сравнения» появляется счётчик.
- На /compare/ панель скрыта; список синхронизируется с открытой таблицей.
- <body data-compare-url="{% url 'compare' %}"> — адрес страницы сравнения для скрипта.
