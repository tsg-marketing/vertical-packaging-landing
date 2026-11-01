# edukursy — страница курса: лендинг + разбор редакции из двух JSON

Шаблон страницы курса = ваш текущий `detail.html` (лендинг из полей курса) + блоки разбора,
которые заполняются из двух полей курса в админке:

- **extract_json** — факты со страницы школы (схема: `schemas/extract_json_prompt.txt`);
- **editorial_json** — текст редакции (схема: `schemas/editorial_json_prompt.txt`).

**Главное правило:** блок выводится, только если в JSON есть ключ и в нём есть данные.
`null`, `""`, `[]`, `{}` или отсутствующий ключ — блок пропускается целиком, вместе с заголовком и пунктом навигации.

Промпт для агента — в `PROMPT.md`.

---

## 1. Какие блоки и откуда берутся

| Блок на странице | Ключи | Если пусто |
|---|---|---|
| Описание под H1 | `editorial.editorial_intro` → `extract.short_summary` | `course.description` (как сейчас) |
| Факты-плашки под H1 | `level`, `format`, `duration_text`, `certificate`, `employment_support` | ваш старый `facts` из view |
| Цена текстом (справа) | `price_text`, `installment_text` | только если у курса нет числовой цены; иначе — ваш price-box |
| Рассрочка в price-box | `installment_text` | если у курса нет `price_month` |
| О курсе | `editorial.editorial_summary` → `extract.short_summary` (если он не ушёл в лид) + `course_category`, `level`, `format` справа | — |
| Чему вы научитесь | `what_you_learn` | `course.features` (как сейчас) |
| Кому подойдёт / Может не подойти | `for_whom`, `not_for_whom` (редакция → extract) | `course.audience_text` |
| Как проходит обучение | `course_features` (иконка подбирается по словам) + `prerequisites` | — |
| Преимущества, Программа | — | из полей курса, без изменений |
| Мнение редакции | `pros`, `cons`, `editorial_verdict` (редакция → extract) | — |
| Что уточнить перед покупкой | `editorial.what_to_check_before_buying` | — |
| О школе | — | без изменений |
| Что говорит школа | `extract.source_facts.*` (цитаты) | — |
| Вопросы | FAQ из админки + `editorial.faq` + `extract.faq` без повторов, до 8 | — |

**Правила слияния:**
- если блок есть в обоих JSON (`for_whom`, `not_for_whom`, `pros`, `cons`, `faq`, `editorial_verdict`) — берётся вариант редакции, extract — запасной;
- `extraction_status: "failed"` или `draft_status: "failed"` — этот JSON игнорируется целиком;
- `certificate` / `employment_support`: `true` — «Выдаётся» / «Помощь заявлена», `false` — показываются серым «Не выдаётся» / «Помощь не заявлена», `null` — плашки нет;
- `level` и `format` переводятся на русский (beginner → «С нуля», self-paced → «В своём темпе»…);
- повторяющиеся пункты в списках и вопросы, которые уже есть в FAQ из админки, убираются;
- неверные типы (строка вместо списка, вопрос без ответа, неизвестный level) не ломают страницу — элемент просто пропускается;
- JSON можно вставлять вместе с обёрткой ` ```json ... ``` ` — она снимается автоматически.

Если у курса заполнено поле `content` (HTML-лендинг), блоки лендинга скрываются как сейчас, а блоки разбора из JSON выводятся.

---

## 2. Админка курса

Новый раздел формы **«Разбор курса (JSON)»**:
- два больших моноширинных поля с кнопками «Форматировать», «Вставить пустой шаблон», «Очистить»;
- проверка на лету: «JSON корректный · ключей: 23, заполнено: 21 · статус: ok» или «Ошибка: … (строка 5)», рамка зелёная или красная;
- при сохранении:
  - **ошибка синтаксиса** — не сохраняет: «Ошибка в JSON: строка 1, позиция 22 — … Проверьте запятые и кавычки»;
  - **неверный тип** — не сохраняет: ««certificate»: ожидается true, false или null (без кавычек)», ««level»: допустимо: beginner, …»;
  - **лишние или отсутствующие ключи, статус failed** — сохраняет и показывает предупреждение;
- **«Что выведется на странице»** — список всех 15 блоков: ✓ выведется / — пропущен и из какого ключа взят, «Блоков на странице: 11 из 15» и ссылка на страницу;
- в списке курсов колонка **«Разбор»**: бейджи E ✓/½/✕ и R ✓/½/✕ (extract / редакция: ok / partial / failed / нет),
  фильтр **«Разбор (JSON)»**: оба, только extract, только editorial, нет разбора, статус failed.

---

## 3. Состав пакета
```
course-page-package/
├── README.md, PROMPT.md
├── schemas/                      — ваши промпты-схемы extract_json и editorial_json
├── samples/                      — образцы: полный, частичный, failed
├── app/
│   ├── course_json.py            — сборка блоков, слияние, проверка схем, course_page_for()
│   ├── admin_course_json.py      — CourseJsonAdminMixin, JsonStatusFilter, поле с проверкой
│   ├── templates/course_page/admin/json_textarea.html
│   ├── templatetags/course_json.py — {% course_page course faqs as cpage %}
│   └── tests/test_course_json.py + tests/samples/ — 16 тестов без БД
├── templates/edukursy/courses/
│   ├── detail.html               — ВАШ detail.html + блоки из JSON
│   └── blocks/                   — 10 блоков: facts, about, learn, audience, format, review, check, source, price_text, icon
├── static/edukursy/css/course-page.css
├── static/admin/course_page/     — JS и CSS админки
└── mockups/
    ├── courses/kurs-json/index.html          — все блоки (полные JSON)
    └── courses/kurs-json-partial/index.html  — частичные данные: лишние блоки пропущены
```

Проверено на Django 5.1: 16 тестов, рендер 4 курсов (полный, частичный, без JSON, failed),
сохранение из админки с ```json-обёрткой, ошибки синтаксиса и типов.
