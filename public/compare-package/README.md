# edukursy — сравнение курсов (отдельный пакет для Django)

Сравнение без ограничения по количеству курсов: кнопка «Сравнить» в каталоге и на странице курса,
плавающая панель с выбранными курсами, страница /compare/ с широкой таблицей.

Пошаговый промпт для Cline — в файле PROMPT.md.

## Состав

```
compare-package/
├── README.md
├── PROMPT.md                        — промпт для Cline (одна задача)
├── static/edukursy/
│   ├── js/compare.js                — кнопки, панель, счётчик в меню, стрелки таблицы
│   └── css/compare.css              — стили (НЕ нужен, если подключён полный style.css)
├── templates/edukursy/
│   ├── partials/compare/
│   │   ├── button.html              — кнопка (варианты card / block / inline / icon)
│   │   ├── link.html                — «Перейти к сравнению (N)»
│   │   ├── scripts.html             — подключение JS в base.html
│   │   └── _icons.html
│   └── compare/compare.html         — страница /compare/
├── app/                             — Python-код → в приложение каталога
│   ├── compare_utils.py             — разбор списка, SQL одним запросом, строки таблицы, «лучшее», итоги
│   ├── views_compare.py             — view /compare/ (ROW_SPECS — какие строки показывать)
│   ├── context_processors.py        — выбранные курсы из cookie → кнопки рендерятся сразу нажатыми
│   ├── templatetags/compare_tags.py — фильтры compare_id, ru_plural, тег compare_url_without
│   └── tests/test_compare_utils.py  — тесты логики (SimpleTestCase, без БД)
└── mockups/                         — эталон вида, открывается в браузере
    ├── courses/index.html                       — каталог с кнопками
    ├── courses/python-razrabotchik/index.html   — страница курса
    └── compare/index.html                       — таблица на 6 курсов
```

## Как работает

- Идентификатор курса — `"<school_slug>/<course_slug>"`.
- Выбор хранится в браузере (localStorage) и дублируется в cookie `edukursy_compare`.
  Регистрация и новые таблицы в БД не нужны.
- Ограничения по количеству нет. Если курсов очень много (больше ~100) и cookie переполняется
  (лимит браузера ~4 КБ), в cookie попадают первые курсы, а полный список остаётся в браузере и в ссылке.
- Панель снизу: курсы в одну строку с горизонтальной прокруткой и стрелками.
- Страница /compare/: колонки фиксированной ширины, первая колонка закреплена, стрелки «1–5 из 12»
  появляются, только когда всё не помещается.
- Нужно, чтобы в базе были поля `School.slug`, `Course.slug`, `Course.school` (FK), `Course.price`.
  Остальные поля таблицы — необязательные: строка, по которой ни у одного курса нет данных, не выводится.
