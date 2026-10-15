# edukursy — пакет для переноса в Django

Подробная инструкция: страница /main/instruction (или файл PROMPTS.md).

## Состав

```
django-export/
├── README.md            — этот файл
├── PROMPTS.md           — промпты для Cline по шагам (0–10)
├── DATA_MAP.md          — какие данные нужны каждой странице и что делать, если их нет
├── .clinerules          — правила проекта для Cline (положить в корень Django-проекта)
├── static/edukursy/     — готовая статика → в папку static/ Django
│   ├── css/style.css    — все стили (один файл, без сборки)
│   ├── js/script.js     — меню, фильтры на мобильном, сортировка, FAQ (ванильный JS)
│   └── img/             — логотип, заглушки, обложки
└── mockups/             — HTML-макеты (эталон), открываются в браузере
    ├── index.html                        → / (главная)
    ├── professions/                      → /professions/
    ├── professions/backend-razrabotchik/ → /professions/<slug>/
    ├── courses/                          → /courses/
    ├── courses/python-razrabotchik/      → /courses/<school>/<course>/
    ├── schools/                          → /schools/
    ├── schools/school_name/              → /schools/<slug>/
    ├── compare/                          → /compare/
    ├── blog/                             → /blog/
    └── blog/kak-sravnivat-ceny-kursov/   → /blog/<slug>/
```

## Разметка в макетах

- `<!-- DATA: course.price -->` — сюда подставляется значение из БД.
- `<!-- DATA: цикл по ... -->` — первая карточка = образец для `{% for %}`.
- `<!-- AD SLOT: N, ... -->` — рекламный блок.
- Картинки `school-*.jpg`, `blog-*.jpg` — демо, в проде заменяются данными.
