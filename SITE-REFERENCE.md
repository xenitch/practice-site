# Референс: как устроен сайт xenitch.ru

Документация для воспроизведения: по этому файлу агент в другом проекте может собрать сайт в том же стиле и на той же технологии. Всё необходимое (код генератора, шаблоны, CSS, рабочие процессы) включено сюда целиком — заглядывать в исходный репозиторий не обязательно, но он открыт: https://github.com/xenitch/practice-site

## 1. Архитектура в двух абзацах

Статический сайт без JavaScript: собственный генератор `build.py` (~60 строк Python) превращает markdown-файлы с frontmatter из `content/` в HTML по Jinja2-шаблонам из `templates/` и складывает результат в `docs/`. Папку `docs/` раздаёт GitHub Pages (ветка `main`, настройка «serve from /docs»), домен привязан через файл `docs/CNAME` и A-записи у DNS-провайдера. Публикация = `python build.py` + `git push`; никакого CI, что собрано локально — то и опубликовано.

Дизайн — «книжная типографика, английский клуб, old money»: бумага цвета слоновой кости, чернильно-коричневый текст, акценты гоночный зелёный и бордо, тонкие золотистые линейки, шрифты с кириллицей Playfair Display (заголовки) + Literata (текст), self-hosted woff2, малые прописные, буквицы, флероны ❦ вместо горизонтальных линеек, колонка ~65 знаков.

## 2. Раскладка репозитория

```
site/
├── content/                 # источник: markdown с frontmatter
│   ├── index.md             # главная  → /
│   └── research/
│       ├── index.md         # хаб раздела → /research/
│       ├── regular.md       # подстраница → /research/regular/
│       ├── communities.md   # подстраница со списком статей → /research/communities/
│       └── {slug}.md        # статьи → /research/{slug}/
├── templates/               # Jinja2: base.html, page.html, article.html, research.html
├── static/
│   ├── style.css
│   └── fonts/*.woff2        # 6 файлов: 2 семейства × (regular, 700, italic)
├── build.py                 # генератор
├── tests/test_build.py      # pytest, ~10 тестов
├── requirements.txt         # markdown, python-frontmatter, jinja2, pytest
├── docs/                    # РЕЗУЛЬТАТ сборки — коммитится, его раздаёт GitHub Pages
│   └── CNAME                # генерируется build.py из SITE["domain"]
└── README.md
```

Правила URL (генератор): `content/index.md → /`; `content/research/index.md → /research/`; `content/research/foo.md → /research/foo/` (каждая страница — папка с `index.html`, «pretty URLs»).

## 3. Генератор — build.py целиком

Зависимости (Python 3.9+, в project-local venv): `Markdown`, `python-frontmatter` (на Python 3.9 нужен пин `python-frontmatter==1.0.1`; на 3.10+ подойдёт свежий), `Jinja2`, `pytest`.

```python
#!/usr/bin/env python3
"""Сборка сайта: content/ + templates/ -> docs/."""
from pathlib import Path, PurePosixPath
import shutil

import frontmatter
import markdown
from jinja2 import Environment, FileSystemLoader

SITE = {
    "name": "Сообщества совместной практики",      # ← заменить под новый сайт
    "domain": "xenitch.ru",                         # ← заменить
    "author": "Ксения Костюченко",                  # ← заменить
    "telegram": "https://t.me/xenitch",             # ← заменить
    "description": "Живые группы совместной практики и исследование того, почему практика повторяется.",
}


def page_url(rel: PurePosixPath) -> str:
    parts = rel.parent.parts if rel.name == "index.md" else rel.parent.parts + (rel.stem,)
    return "/" + "/".join(parts) + "/" if parts else "/"


def render_md(text: str) -> str:
    return markdown.markdown(text, extensions=["extra"])


def load_page(path: Path, content_dir: Path) -> dict:
    post = frontmatter.load(path)
    rel = PurePosixPath(path.relative_to(content_dir).as_posix())
    url = page_url(rel)
    return {
        "url": url,
        "meta": post.metadata,
        "content": render_md(post.content),
        "is_article": url.startswith("/research/") and url != "/research/",
    }


def build(root: Path) -> None:
    content_dir, out = root / "content", root / "docs"
    env = Environment(loader=FileSystemLoader(root / "templates"), autoescape=False)
    pages = [load_page(p, content_dir) for p in sorted(content_dir.rglob("*.md"))]
    # Карточка в списке — только у статей (у них есть date); служебные страницы раздела без date не попадают
    articles = sorted((p for p in pages if p["is_article"] and p["meta"].get("date")),
                      key=lambda p: str(p["meta"].get("date", "")), reverse=True)
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(root / "static", out / "static")
    (out / "CNAME").write_text(SITE["domain"], encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    for page in pages:
        tpl = page["meta"].get("template") or ("article.html" if page["is_article"] else "page.html")
        html = env.get_template(tpl).render(site=SITE, page=page, articles=articles)
        dest = out / page["url"].strip("/") / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    build(Path(__file__).parent)
    print("Собрано в docs/")
```

Ключевые решения, которые стоит сохранить в новом проекте:
- `autoescape=False` + фильтр `| e` на всех frontmatter-значениях в шаблонах (контент — доверенный HTML из markdown, метаданные экранируются).
- Список статей строится автоматически из frontmatter — никаких индексов руками. Признак статьи: лежит в разделе И имеет `date`. Страницы раздела без `date` в список не попадают.
- `docs/` полностью пересоздаётся при каждой сборке (`rmtree`) — устаревшие файлы не залёживаются.
- Название раздела `research/` захардкожено в `is_article` — при другом имени раздела заменить строку.

## 4. Конвенции контента

Frontmatter страницы: `title`, `description` (для meta и карточки), опционально `template` (переопределяет выбор шаблона). Статья дополнительно: `subtitle` (опционально), `date` в формате ГГГГ-ММ-ДД (обязательно — по ней сортировка и признак «статьи»).

```markdown
---
title: Инклинги
subtitle: Как кружок друзей без единого правила породил «Властелина колец»
date: 2026-07-07
description: Одна фраза для карточки в списке статей.
---
Текст статьи. H1 не нужен — заголовок рендерит шаблон article.html из frontmatter.
```

Нюансы markdown (расширение `extra`): сырой HTML пропускается (используется для спецразметки вроде `<ol class="mechanisms">` и карточек-ссылок); строки вида `1)` в начале абзаца экранировать как `1\)`; разделитель `---` в тексте рендерится флероном ❦.

## 5. Шаблоны — целиком

`templates/base.html` (заменить название раздела и подпись под свой проект):

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% if page.meta.title and page.url != '/' %}{{ page.meta.title | e }} — {{ site.name | e }}{% else %}{{ site.name | e }}{% endif %}</title>
  <meta name="description" content="{{ (page.meta.description or site.description) | e }}">
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <header class="site-header">
    <a class="site-name" href="/">{{ site.name | e }}</a>
    <nav class="site-nav"><a href="/research/"{% if page.url.startswith('/research/') %} class="current"{% endif %}>Исследование</a></nav>
  </header>
  <main>{% block content %}{% endblock %}</main>
  <footer class="site-footer">
    <p>{{ site.author | e }} · <a href="{{ site.telegram }}">@xenitch</a></p>
  </footer>
</body>
</html>
```

`templates/page.html` — обычная страница:

```html
{% extends "base.html" %}
{% block content %}<article class="prose">{{ page.content }}</article>{% endblock %}
```

`templates/article.html` — статья (кикер, заголовок из frontmatter, буквица через CSS, возврат к списку):

```html
{% extends "base.html" %}
{% block content %}
<article class="prose article">
  <header class="article-header">
    <p class="kicker">Разбор</p>
    <h1>{{ page.meta.title | e }}</h1>
    {% if page.meta.subtitle %}<p class="subtitle">{{ page.meta.subtitle | e }}</p>{% endif %}
  </header>
  {{ page.content }}
  <p class="backlink"><a href="/research/communities/">← К сообществам практики</a></p>
</article>
{% endblock %}
```

`templates/research.html` — страница со списком статей (текст + карточки, автогенерация):

```html
{% extends "base.html" %}
{% block content %}
<article class="prose">{{ page.content }}</article>
<section class="cards">
  <h2 class="kicker">Разборы</h2>
  {% for a in articles %}
  <a class="card" href="{{ a.url }}">
    <h3>{{ a.meta.title | e }}</h3>
    {% if a.meta.description %}<p>{{ a.meta.description | e }}</p>{% endif %}
  </a>
  {% endfor %}
</section>
{% endblock %}
```

Приём для страницы-оглавления (карточки-ссылки без автосписка) — сырой HTML прямо в markdown:

```html
<section class="cards">
<a class="card" href="/research/regular/">
<h3>Регулярная практика</h3>
<p>Подпись карточки одной фразой.</p>
</a>
</section>
```

## 6. Дизайн-система — style.css целиком

Палитра «английский клуб»: бумага `#f6f1e5`, чернила `#2b2118`, гоночный зелёный `#1f4a38` (ссылки, акценты), бордо `#6e1f2e` (hover, кикеры), золото `#b08d3f` (линейки, орнаменты), приглушённый `#6d6152` (вторичный текст). Для другого сайта «в похожем стиле» можно сдвинуть акцентную пару (зелёный/бордо → синий/терракота и т. п.), сохранив бумагу, чернила и золото.

```css
/* Палитра: бумага/чернила/клубные акценты */
:root {
  --paper: #f6f1e5; --ink: #2b2118; --green: #1f4a38; --claret: #6e1f2e;
  --gold: #b08d3f; --muted: #6d6152;
}
@font-face { font-family: "Playfair Display"; src: url(/static/fonts/playfair-display-v40-cyrillic_latin-regular.woff2) format("woff2"); font-weight: 400; font-display: swap; }
@font-face { font-family: "Playfair Display"; src: url(/static/fonts/playfair-display-v40-cyrillic_latin-700.woff2) format("woff2"); font-weight: 700; font-display: swap; }
@font-face { font-family: "Playfair Display"; src: url(/static/fonts/playfair-display-v40-cyrillic_latin-italic.woff2) format("woff2"); font-style: italic; font-display: swap; }
@font-face { font-family: "Literata"; src: url(/static/fonts/literata-v40-cyrillic_latin-regular.woff2) format("woff2"); font-weight: 400; font-display: swap; }
@font-face { font-family: "Literata"; src: url(/static/fonts/literata-v40-cyrillic_latin-700.woff2) format("woff2"); font-weight: 700; font-display: swap; }
@font-face { font-family: "Literata"; src: url(/static/fonts/literata-v40-cyrillic_latin-italic.woff2) format("woff2"); font-style: italic; font-display: swap; }

html { background: var(--paper); color: var(--ink); }
body {
  margin: 0 auto; padding: 2.5rem 1.25rem 4rem; max-width: 42rem;
  font: 400 1.125rem/1.65 "Literata", "PT Serif", Georgia, serif;
  hyphens: auto; font-feature-settings: "onum" 1;
}
h1, h2, h3 { font-family: "Playfair Display", Georgia, serif; line-height: 1.2; font-weight: 700; }
h1 { font-size: 2.1rem; margin: 0.4em 0; }
a { color: var(--green); text-decoration-color: color-mix(in srgb, var(--gold) 60%, transparent); text-underline-offset: 3px; }
a:hover { color: var(--claret); }
.kicker, .site-nav a, .site-name { font-variant-caps: all-small-caps; letter-spacing: 0.08em; }
.site-header { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem;
  border-bottom: 1px solid var(--gold); padding-bottom: 0.75rem; margin-bottom: 2.5rem; }
.site-name { text-decoration: none; color: var(--ink); font-family: "Playfair Display", serif; }
.kicker { color: var(--claret); margin: 0; }
.subtitle { font-style: italic; color: var(--muted); font-size: 1.2rem; }
.article > p:first-of-type::first-letter, .article .article-header + p::first-letter {
  font-family: "Playfair Display", serif; font-size: 3.2em; float: left;
  line-height: 0.85; padding: 0.04em 0.08em 0 0; color: var(--green); }
blockquote { margin: 1.5em 0; padding-left: 1.25em; border-left: 2px solid var(--gold);
  font-style: italic; color: var(--muted); }
hr { border: 0; text-align: center; margin: 2.5em 0; }
hr::after { content: "❦"; color: var(--gold); font-size: 1.1em; }
table { border-collapse: collapse; width: 100%; font-size: 0.9em; display: block; overflow-x: auto; }
th, td { border-top: 1px solid color-mix(in srgb, var(--gold) 40%, transparent);
  padding: 0.5em 0.75em; text-align: left; vertical-align: top; }
th { font-variant-caps: all-small-caps; letter-spacing: 0.06em; }
.mechanisms { counter-reset: mech; list-style: none; padding: 0; }
.mechanisms li { counter-increment: mech; margin: 1.1em 0; padding-left: 2.4rem; position: relative; }
.mechanisms li::before { content: counter(mech); position: absolute; left: 0; top: -0.1em;
  font-family: "Playfair Display", serif; font-size: 1.6em; color: var(--gold); }
.cards { margin-top: 3rem; }
.card { display: block; text-decoration: none; color: inherit; padding: 1.25rem 1.5rem;
  border: 1px solid color-mix(in srgb, var(--gold) 50%, transparent); margin: 1rem 0; }
.card:hover { border-color: var(--claret); }
.card h3 { margin: 0 0 0.4em; color: var(--green); }
.card p { margin: 0; color: var(--muted); font-size: 0.95em; }
.site-footer { margin-top: 4rem; border-top: 1px solid var(--gold); padding-top: 1rem;
  color: var(--muted); font-size: 0.9em; }
.backlink { margin-top: 3rem; }
```

Типографические принципы, зашитые в этот CSS: колонка `max-width: 42rem` ≈ 65 знаков; кегль 18px (`1.125rem`) с интерлиньяжем 1.65; старостильные цифры (`"onum" 1`); переносы `hyphens: auto` (требует `lang="ru"` на `<html>`); малые прописные для навигации и рубрик; буквица в первом абзаце статьи; никаких теней, скруглений и анимаций — только цвет, линейка, шрифт. Оговорка: `color-mix()` требует браузеров 2023+; для максимальной совместимости заменить на полупрозрачные rgba.

## 7. Шрифты: как получить woff2

Источник — google-webfonts-helper (сабсеты latin+cyrillic, только woff2):

```bash
curl -sL "https://gwfh.mranftl.com/api/fonts/playfair-display?download=zip&subsets=cyrillic,latin&formats=woff2&variants=regular,italic,700" -o pd.zip
curl -sL "https://gwfh.mranftl.com/api/fonts/literata?download=zip&subsets=cyrillic,latin&formats=woff2&variants=regular,italic,700" -o lit.zip
unzip -o pd.zip -d static/fonts && unzip -o lit.zip -d static/fonts
```

После скачивания сверить имена файлов с `@font-face` (версия в имени, например `v40`, со временем меняется — поправить в CSS). Для другого характера сайта можно заменить семейства (у обоих обязательна кириллица), сохранив схему «контрастная антиква для заголовков + читабельная антиква для текста».

## 8. Рабочие процессы

```bash
# первичная настройка
python3 -m venv .venv
.venv/bin/pip install markdown python-frontmatter jinja2 pytest
.venv/bin/pip freeze | grep -iE "^(markdown|python-frontmatter|jinja2|pytest)=" > requirements.txt

# цикл работы
.venv/bin/python build.py && .venv/bin/pytest tests/ -q   # собрать + тесты
cd docs && python3 -m http.server 8899                     # локальное превью
git add -A && git commit -m "..." && git push              # публикация (~1 мин до продакшена)
```

Тесты (pytest, `tests/test_build.py`) держат инварианты: маппинг URL; рендер markdown (таблицы); frontmatter; полный прогон `build()` во временную папку (наличие index.html всех страниц, CNAME, .nojekyll, копия static); сортировка статей новые-первыми; исключение бездатных страниц из списка; идемпотентность (устаревший файл в docs/ исчезает после пересборки). При любом изменении build.py — сначала тест, потом код.

## 9. Публикация: GitHub Pages + домен

1. Репозиторий на GitHub, ветка `main`, в корне — всё из раздела 2 (включая собранный `docs/`).
2. Включить Pages: Settings → Pages → «Deploy from a branch» → `main` + `/docs`. Через API: `POST /repos/{owner}/{repo}/pages` с `{"source":{"branch":"main","path":"/docs"}}`.
3. Файл `docs/CNAME` с доменом генерирует build.py — GitHub подхватит его сам.
4. DNS у регистратора/DNS-хостинга домена:
   - `@ A` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `www CNAME` → `{github-логин}.github.io.`
   - ⚠️ если на домене есть почта — перенести/сохранить её MX-, SPF- (TXT) и DKIM-записи, иначе почта умрёт.
5. Дождаться выпуска сертификата (от минут до часов; если завис — снять и заново указать домен в настройках Pages), затем включить «Enforce HTTPS».
6. Проверка: корень, www, все страницы отвечают 200 по HTTPS; `dig` показывает нужные A-записи.
7. Нюанс: при смене custom domain через настройки GitHub сам коммитит правку `CNAME` в репозиторий — перед следующим `git push` сделать `git pull --rebase`.

## 10. Чеклист адаптации под новый сайт

- [ ] `SITE` в build.py: название, домен, автор, контакт, описание
- [ ] Имя раздела со статьями: заменить `research/` в `is_article` (build.py), в nav (base.html), в backlink (article.html), создать `content/{раздел}/`
- [ ] base.html: пункты навигации и подпись в подвале
- [ ] article.html: текст кикера («Разбор» → своё) и текст/адрес backlink
- [ ] research.html: заголовок списка («Разборы» → своё)
- [ ] Палитра в `:root` (сохранить логику: бумага/чернила/два акцента/золото/приглушённый)
- [ ] Шрифты: скачать, сверить имена файлов в @font-face
- [ ] `lang` в base.html, если сайт не на русском
- [ ] Контент: `content/index.md` + раздел; статьи обязаны иметь `date`
- [ ] Прогнать тесты, поправив в них домен из CNAME-проверки
