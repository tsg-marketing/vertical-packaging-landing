"""
Страница курса из двух JSON: extract_json (факты со страницы школы) и editorial_json (текст редакции).

Главное правило: блок выводится, только если в JSON есть ключ и в нём есть данные
(не null, не "", не [] и не {}). Иначе блок молча пропускается.

    page = build_course_page(course)          # в view
    {% if page.learn %}...{% endif %}         # в шаблоне

Если extraction_status / draft_status == "failed" — этот JSON целиком игнорируется.
Если в обоих JSON есть одинаковый по смыслу блок (for_whom, pros, cons, faq, verdict),
берётся вариант редакции (editorial_json), а extract_json — запасной.
"""
import json
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

# ---------- схемы (для проверки в админке) ----------
EXTRACT_KEYS = {
    "source_url": "str", "extraction_status": "enum:ok,partial,failed",
    "course_title": "str", "school_name": "str", "course_category": "str",
    "level": "enum:beginner,beginner_plus,intermediate,advanced,mixed",
    "format": "list_enum:online,recorded,live,mentoring,self-paced",
    "duration_text": "str", "price_text": "str", "installment_text": "str",
    "certificate": "bool", "employment_support": "bool", "short_summary": "str",
    "for_whom": "list_str", "not_for_whom": "list_str", "what_you_learn": "list_str",
    "course_features": "list_str", "pros": "list_str", "cons": "list_str",
    "prerequisites": "list_str", "faq": "faq", "editorial_verdict": "str",
    "source_facts": "facts",
}
SOURCE_FACT_KEYS = ["description_excerpt", "pricing_excerpt", "duration_excerpt", "format_excerpt", "employment_excerpt", "certificate_excerpt"]
EDITORIAL_KEYS = {
    "source_url": "str", "draft_status": "enum:ok,partial,failed",
    "course_title": "str", "school_name": "str",
    "editorial_intro": "str", "editorial_summary": "str",
    "for_whom": "list_str", "not_for_whom": "list_str", "pros": "list_str", "cons": "list_str",
    "what_to_check_before_buying": "list_str", "faq": "faq", "editorial_verdict": "str",
}

LEVELS = {
    "beginner": "С нуля",
    "beginner_plus": "Для начинающих с базой",
    "intermediate": "Средний уровень",
    "advanced": "Продвинутый уровень",
    "mixed": "Для разных уровней",
}
FORMATS = {
    "online": "Онлайн",
    "recorded": "Уроки в записи",
    "live": "Живые занятия",
    "mentoring": "С наставником",
    "self-paced": "В своём темпе",
}
SOURCE_FACT_LABELS = {
    "description_excerpt": "О курсе",
    "pricing_excerpt": "Стоимость",
    "duration_excerpt": "Длительность",
    "format_excerpt": "Формат",
    "employment_excerpt": "Трудоустройство",
    "certificate_excerpt": "Документ",
}

# Иконка для пункта «Как устроено обучение» — по ключевым словам
FEATURE_ICONS = [
    ("mentor", ("наставник", "ментор", "куратор", "mentor", "проверк")),
    ("project", ("проект", "портфолио", "кейс", "project", "portfolio")),
    ("clock", ("график", "темп", "запис", "в любое время", "schedule", "self")),
    ("video", ("вебинар", "живы", "онлайн-занят", "трансляц", "live", "webinar")),
    ("career", ("карьер", "резюме", "трудоустр", "собеседован", "ваканс", "career", "job")),
    ("doc", ("диплом", "сертификат", "удостоверен", "документ", "certificate")),
    ("chat", ("чат", "сообщество", "комьюнити", "community")),
]


# ---------- разбор входных данных ----------
FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.I)


def parse_json(value):
    """dict из JSONField / строки / строки с ```json ... ```. Ошибка → ValueError."""
    if value in (None, "", b""):
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if isinstance(value, str):
        text = FENCE_RE.sub("", value.strip()).strip()
        if not text:
            return {}
        data = json.loads(text)
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise ValueError("Ожидается JSON-объект { ... }, а не список или строка.")
        return data
    raise ValueError("Неподдерживаемый тип данных JSON.")


def _safe(value):
    try:
        return parse_json(value)
    except (ValueError, TypeError):
        return {}


def has(data, key):
    """Ключ есть и в нём есть данные."""
    if key not in data:
        return False
    v = data[key]
    if v is None:
        return False
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, (list, dict)):
        return bool(v)
    return True


def text(data, key):
    if not has(data, key) or not isinstance(data[key], str):
        return ""
    return data[key].strip()


def str_list(data, key):
    if not has(data, key) or not isinstance(data[key], list):
        return []
    out, seen = [], set()
    for item in data[key]:
        if isinstance(item, str) and item.strip():
            norm = item.strip().lower().rstrip(".")
            if norm not in seen:
                seen.add(norm)
                out.append(item.strip())
    return out


def faq_list(data):
    if not has(data, "faq") or not isinstance(data["faq"], list):
        return []
    out = []
    for item in data["faq"]:
        if isinstance(item, dict):
            q, a = str(item.get("question") or "").strip(), str(item.get("answer") or "").strip()
            if q and a:
                out.append({"question": q, "answer": a})
    return out


def tri_state(data, key):
    """True / False / None. Строки "true"/"false" тоже понимаем."""
    if key not in data:
        return None
    v = data[key]
    if isinstance(v, bool):
        return v
    if isinstance(v, str) and v.strip().lower() in ("true", "false"):
        return v.strip().lower() == "true"
    return None


def _norm_q(q):
    return re.sub(r"[^\w]+", " ", q.lower().replace("ё", "е")).strip()


def feature_icon(label):
    low = label.lower()
    for icon, words in FEATURE_ICONS:
        if any(w in low for w in words):
            return icon
    return "dot"


# ---------- результат ----------
@dataclass
class Fact:
    key: str
    label: str
    value: str
    icon: str
    tone: str = ""


@dataclass
class CoursePage:
    extract_ok: bool = False
    editorial_ok: bool = False
    extract_status: str = ""
    editorial_status: str = ""

    lead: str = ""
    lead_source: str = ""
    category: str = ""
    level: str = ""
    level_code: str = ""
    formats: list = field(default_factory=list)
    facts: list = field(default_factory=list)
    price_text: str = ""
    installment_text: str = ""

    summary: str = ""
    learn: list = field(default_factory=list)
    for_whom: list = field(default_factory=list)
    not_for_whom: list = field(default_factory=list)
    features: list = field(default_factory=list)
    prerequisites: list = field(default_factory=list)
    pros: list = field(default_factory=list)
    cons: list = field(default_factory=list)
    check: list = field(default_factory=list)
    verdict: str = ""
    verdict_source: str = ""
    faq: list = field(default_factory=list)
    source_facts: list = field(default_factory=list)
    source_url: str = ""
    source_domain: str = ""
    show_source_link: bool = False

    @property
    def has_audience(self):
        return bool(self.for_whom or self.not_for_whom)

    @property
    def has_review(self):
        return bool(self.pros or self.cons or self.verdict)

    @property
    def is_empty(self):
        return not any([self.lead, self.facts, self.summary, self.learn, self.has_audience, self.features,
                        self.prerequisites, self.has_review, self.check, self.faq, self.source_facts])

    def tabs(self, extra=None):
        """Пункты навигации по странице — только для выводимых блоков."""
        items = []
        if self.summary:
            items.append(("course-about", "О курсе"))
        if self.learn:
            items.append(("course-skills", "Чему научитесь"))
        if self.has_audience:
            items.append(("course-audience", "Кому подойдёт"))
        if self.features:
            items.append(("course-format", "Как проходит обучение"))
        if self.has_review:
            items.append(("course-review", "Мнение редакции"))
        if self.check:
            items.append(("course-check", "Что уточнить"))
        return items + list(extra or [])

    def report(self):
        """Для админки: какие блоки выведутся и откуда взяты данные."""
        rows = [
            ("Описание под заголовком", bool(self.lead), self.lead_source or "editorial_intro → short_summary"),
            ("Факты: уровень, формат, длительность…", bool(self.facts), "level, format, duration_text, certificate, employment_support, installment_text"),
            ("Цена текстом (если в курсе нет цены)", bool(self.price_text), "price_text"),
            ("О курсе", bool(self.summary), "editorial_summary → short_summary"),
            ("Чему вы научитесь", bool(self.learn), "what_you_learn"),
            ("Кому подойдёт", bool(self.for_whom), "editorial.for_whom → extract.for_whom"),
            ("Кому может не подойти", bool(self.not_for_whom), "editorial.not_for_whom → extract.not_for_whom"),
            ("Как проходит обучение", bool(self.features), "course_features"),
            ("Что нужно для старта", bool(self.prerequisites), "prerequisites"),
            ("Плюсы", bool(self.pros), "editorial.pros → extract.pros"),
            ("Минусы", bool(self.cons), "editorial.cons → extract.cons"),
            ("Вердикт редакции", bool(self.verdict), self.verdict_source or "editorial.editorial_verdict → extract.editorial_verdict"),
            ("Что уточнить перед покупкой", bool(self.check), "what_to_check_before_buying"),
            ("Факты со страницы школы", bool(self.source_facts), "source_facts.*"),
            ("Вопросы и ответы", bool(self.faq), f"editorial.faq + extract.faq ({len(self.faq)})"),
        ]
        return rows


def build_course_page(course=None, extract=None, editorial=None, skip_questions=(), max_faq=8):
    """
    course — объект курса с полями extract_json / editorial_json (или передайте extract/editorial напрямую).
    skip_questions — вопросы, которые уже есть в FAQ из админки (чтобы не дублировать).
    """
    ex = _safe(extract if extract is not None else getattr(course, "extract_json", None))
    ed = _safe(editorial if editorial is not None else getattr(course, "editorial_json", None))
    page = CoursePage()

    page.extract_status = str(ex.get("extraction_status") or "")
    page.editorial_status = str(ed.get("draft_status") or "")
    if page.extract_status == "failed":
        ex = {}
    if page.editorial_status == "failed":
        ed = {}
    page.extract_ok = bool(ex)
    page.editorial_ok = bool(ed)

    # Лид под заголовком
    if text(ed, "editorial_intro"):
        page.lead, page.lead_source = text(ed, "editorial_intro"), "editorial_intro"
    elif text(ex, "short_summary"):
        page.lead, page.lead_source = text(ex, "short_summary"), "short_summary"

    # О курсе — без повтора лида
    summary = text(ed, "editorial_summary")
    if not summary and page.lead_source != "short_summary":
        summary = text(ex, "short_summary")
    page.summary = summary

    # Факты
    page.category = text(ex, "course_category")
    level = text(ex, "level")
    if level in LEVELS:
        page.level, page.level_code = LEVELS[level], level
        page.facts.append(Fact("level", "Уровень", LEVELS[level], "level"))
    page.formats = [FORMATS[f] for f in (ex.get("format") or []) if isinstance(f, str) and f in FORMATS]
    if page.formats:
        page.facts.append(Fact("format", "Формат", ", ".join(page.formats), "format"))
    if text(ex, "duration_text"):
        page.facts.append(Fact("duration", "Длительность", text(ex, "duration_text"), "clock"))
    cert = tri_state(ex, "certificate")
    if cert is not None:
        page.facts.append(Fact("certificate", "Документ", "Выдаётся" if cert else "Не выдаётся", "doc", "" if cert else "muted"))
    job = tri_state(ex, "employment_support")
    if job is not None:
        page.facts.append(Fact("employment", "Трудоустройство", "Помощь заявлена" if job else "Помощь не заявлена", "career", "" if job else "muted"))
    page.price_text = text(ex, "price_text")
    page.installment_text = text(ex, "installment_text")

    # Списки
    page.learn = str_list(ex, "what_you_learn")
    page.features = [{"text": f, "icon": feature_icon(f)} for f in str_list(ex, "course_features")]
    page.prerequisites = str_list(ex, "prerequisites")
    page.for_whom = str_list(ed, "for_whom") or str_list(ex, "for_whom")
    page.not_for_whom = str_list(ed, "not_for_whom") or str_list(ex, "not_for_whom")
    page.pros = str_list(ed, "pros") or str_list(ex, "pros")
    page.cons = str_list(ed, "cons") or str_list(ex, "cons")
    page.check = str_list(ed, "what_to_check_before_buying")

    if text(ed, "editorial_verdict"):
        page.verdict, page.verdict_source = text(ed, "editorial_verdict"), "editorial.editorial_verdict"
    elif text(ex, "editorial_verdict"):
        page.verdict, page.verdict_source = text(ex, "editorial_verdict"), "extract.editorial_verdict"

    # FAQ: редакция → факты, без дублей (в т.ч. с FAQ из админки)
    seen = {_norm_q(q) for q in skip_questions if q}
    for item in faq_list(ed) + faq_list(ex):
        key = _norm_q(item["question"])
        if key in seen:
            continue
        seen.add(key)
        page.faq.append(item)
    page.faq = page.faq[:max_faq]

    # Источник
    facts = ex.get("source_facts") if isinstance(ex.get("source_facts"), dict) else {}
    for key in SOURCE_FACT_KEYS:
        if text(facts, key):
            page.source_facts.append({"key": key, "label": SOURCE_FACT_LABELS[key], "text": text(facts, key)})
    url = text(ex, "source_url") or text(ed, "source_url")
    if url.startswith(("http://", "https://")):
        page.source_url = url
        page.source_domain = urlparse(url).netloc.removeprefix("www.")
    return page


# ---------- проверка JSON для админки ----------
def _check_type(kind, value):
    if value is None:
        return None
    if kind == "str":
        return None if isinstance(value, str) else "ожидается строка или null"
    if kind == "bool":
        return None if isinstance(value, bool) else "ожидается true, false или null (без кавычек)"
    if kind.startswith("enum:"):
        allowed = kind[5:].split(",")
        return None if value in allowed else f"допустимо: {', '.join(allowed)}"
    if kind == "list_str":
        if not isinstance(value, list):
            return "ожидается список [ ]"
        bad = [i for i, v in enumerate(value) if not isinstance(v, str)]
        return f"элементы {bad} — не строки" if bad else None
    if kind.startswith("list_enum:"):
        if not isinstance(value, list):
            return "ожидается список [ ]"
        allowed = kind[10:].split(",")
        bad = [v for v in value if v not in allowed]
        return f"недопустимые значения {bad}; допустимо: {', '.join(allowed)}" if bad else None
    if kind == "faq":
        if not isinstance(value, list):
            return "ожидается список [ {question, answer} ]"
        for i, item in enumerate(value):
            if not isinstance(item, dict) or not str(item.get("question") or "").strip() or not str(item.get("answer") or "").strip():
                return f"элемент {i + 1}: нужны непустые question и answer"
        return None
    if kind == "facts":
        if not isinstance(value, dict):
            return "ожидается объект { ... }"
        extra = [k for k in value if k not in SOURCE_FACT_KEYS]
        bad = [k for k in SOURCE_FACT_KEYS if value.get(k) is not None and not isinstance(value.get(k), str)]
        if bad:
            return f"поля {bad} должны быть строкой или null"
        return f"лишние ключи {extra}" if extra else None
    return None


def validate(data, schema):
    """(errors, warnings). Ошибки блокируют сохранение, предупреждения — нет."""
    errors, warnings = [], []
    for key, value in data.items():
        if key not in schema:
            warnings.append(f"«{key}» — неизвестный ключ, на странице не используется")
            continue
        msg = _check_type(schema[key], value)
        if msg:
            if schema[key] == "facts" and msg.startswith("лишние"):
                warnings.append(f"«{key}»: {msg}")
            else:
                errors.append(f"«{key}»: {msg}")
    missing = [k for k in schema if k not in data]
    if data and missing:
        warnings.append("нет ключей (блоки будут пропущены): " + ", ".join(missing))
    return errors, warnings


def validate_extract(data):
    return validate(data, EXTRACT_KEYS)


def validate_editorial(data):
    return validate(data, EDITORIAL_KEYS)


def course_page_for(course, faqs=None):
    """Для view: context["cpage"] = course_page_for(course, faqs). Учитывает настройки COURSE_PAGE_*."""
    from django.conf import settings

    questions = [getattr(f, "question", "") for f in (faqs or [])]
    page = build_course_page(course, skip_questions=questions, max_faq=getattr(settings, "COURSE_PAGE_MAX_FAQ", 8))
    page.show_source_link = getattr(settings, "COURSE_PAGE_SHOW_SOURCE_LINK", False)
    return page
