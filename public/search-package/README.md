# edukursy — строка поиска с подсказками (пакет для Django)

Строка поиска под меню на всех страницах. При вводе от 2 букв выпадают подсказки:
профессии (с числом курсов и ценой «от») и курсы (школа, длительность, цена). Совпадение подсвечено.

Промпт для Cline — в PROMPT.md.

## Возможности
- Поиск по названию курса и профессии, все слова запроса (например «python бэкенд»).
- Без учёта регистра и ё/е — в том числе на SQLite (через поле search_text).
- Неверная раскладка: «ghjuh» → находит «прогр…» и показывает «Показаны результаты по запросу «прогр»».
- Пустое поле: «Вы искали» (последние 5 запросов в браузере) и «Часто ищут».
- Клавиатура: ↑ ↓ выбор, Enter — переход, Esc — закрыть, «/» — фокус на поиск.
- Задержка 220 мс + отмена старых запросов + кэш (браузер и Django cache 5 мин) — сервер не перегружается.
- Кнопка «Найти» / Enter ведёт на страницу результатов /search/?q=...
- Доступность: role="combobox"/"listbox", aria-activedescendant, озвучка числа подсказок.

## Состав
```
search-package/
├── README.md, PROMPT.md
├── static/edukursy/js/search.js        — подсказки (без зависимостей)
├── static/edukursy/css/search.css      — стили строки, выпадашки, страницы результатов
├── templates/edukursy/
│   ├── partials/search_bar.html        — строка поиска → в base.html после </header>
│   ├── partials/search_scripts.html    — подключение JS
│   └── search/results.html             — страница /search/
├── app/
│   ├── search_utils.py                 — нормализация, раскладка, ранжирование, поиск
│   ├── views_search.py                 — search_suggest (JSON) и search_page
│   ├── urls_search.py                  — маршруты /search/ и /search/suggest/
│   ├── context_processors_search.py    — «Часто ищут» из settings.SEARCH_POPULAR
│   ├── models_mixin.py                 — поле search_text (нужно для SQLite)
│   ├── management/commands/rebuild_search_text.py
│   ├── templatetags/search_tags.py     — фильтр highlight
│   └── tests/                          — тесты логики и view
└── mockups/index.html                  — эталон: главная со строкой поиска (работает в браузере на демо-данных)
```

## Формат ответа /search/suggest/?q=pyt
```json
{
  "query": "pyt", "corrected": null,
  "professions": [{"name": "Python-разработчик", "url": "/professions/python-razrabotchik/", "image": "/media/...", "courses_count": 41, "min_price_month": 2900}],
  "courses": [{"name": "Python для бэкенда", "url": "/courses/school-2/python-backend/", "school": "Школа 2", "school_logo": "/media/...", "price": 38000, "price_month": null, "duration": "4 месяца"}],
  "total_professions": 1, "total_courses": 7,
  "popular": ["Python", "Дизайнер"]
}
```

В макете атрибут `data-suggest-demo` и блок `<script id="search-demo">` — только для показа без сервера. На сайте их нет.
